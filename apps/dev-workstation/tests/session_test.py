"""Exercise the shipped session command with only the agent process replaced."""
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dev-session-test-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        (self.home / "work").mkdir()
        self.bin = self.home / "bin"
        self.bin.mkdir()
        self.adapters = self.home / "adapters"
        (self.adapters / "fake").mkdir(parents=True)
        self.executable(self.bin / "flock", "exit 0\n")
        self.executable(self.bin / "claude", "echo unexpected Claude invocation >&2; exit 99\n")
        self.executable(self.home / "seed", 'printf seed >"$1/seeded"\n')
        self.executable(self.adapters / "fake/adapter", r'''
[[ "$1" == run ]] || { echo "$1" >>"$AGENT_STATE_DIR/ops"; exit 0; }
shift
[[ -f seeded ]] || exit 70
n=$(cat "$AGENT_STATE_DIR/calls" 2>/dev/null || echo 0)
n=$((n+1)); echo "$n" >"$AGENT_STATE_DIR/calls"
printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$5" >>"$AGENT_STATE_DIR/args"
if [[ "${FAKE_MODE:-}" == error ]]; then echo 'agent failed' >"$8"; exit 17; fi
if [[ "${FAKE_MODE:-}" == timeout ]]; then sleep 3; fi
if [[ "${FAKE_MODE:-}" == malformed ]]; then echo broken; exit 0; fi
cost=0.04
if [[ "${FAKE_MODE:-}" == cumulative && "$n" == 2 ]]; then cost=0.06; fi
jq -cn --arg cost "$cost" --arg mode "${FAKE_MODE:-incremental}" \
  '{session_id:"resume-1",total_cost_usd:($cost|tonumber),cost_mode:$mode,num_turns:1,permission_denials:[],is_error:false}'
''')
        self.prompt = self.home / "prompt.txt"
        self.prompt.write_text("title: Fixture\nteam: platform\nbudget: 0.10\n---\nFirst {{MCP}}\n--- followup\nNext\n")
        self.env = dict(os.environ, HOME=str(self.home),
                        PATH=f"{self.bin}:{ROOT / 'bin'}:{os.environ['PATH']}",
                        DEVELOPER_AGENT="fake", AGENT_ADAPTERS_DIR=str(self.adapters),
                        AGENT_STATE_DIR=str(self.home / "state"),
                        CODEBASE_SEED=str(self.home / "seed"), SESSION_MODEL="fake-model",
                        SESSION_FOLLOWUP_PERCENT="100", SESSION_ABANDON_PERCENT="0",
                        SESSION_SHORT_TIMEOUT_PERCENT="0", MCP_SERVER_NAME="fixture",
                        AGENT_LOCK=str(self.home / "session.lock"))

    def executable(self, path, text):
        path.write_text(f"#!{BASH}\nset -euo pipefail\n" + text)
        path.chmod(0o755)

    def run_session(self, **env):
        return subprocess.run([BASH, str(ROOT / "bin/dev-session"), str(self.prompt)],
                              env=self.env | env, text=True, capture_output=True, timeout=10)

    def test_incremental_resume_and_remaining_budget(self):
        result = self.run_session()
        self.assertEqual(result.returncode, 0, result.stderr)
        event = json.loads(result.stdout)
        self.assertEqual(event["agent"], "fake")
        self.assertEqual(event["user_turns"], 2)
        self.assertAlmostEqual(event["cost_usd"], 0.08)
        self.assertEqual(event["session_id"], "resume-1")
        args = (self.home / "state/args").read_text().splitlines()
        self.assertEqual(args[0].split("\t"), ["First fixture", "fake-model", "", "0.100000"])
        self.assertEqual(args[1].split("\t"), ["Next", "fake-model", "resume-1", "0.060000"])

    def test_cumulative_cost_is_not_double_counted(self):
        result = self.run_session(FAKE_MODE="cumulative")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertAlmostEqual(json.loads(result.stdout)["cost_usd"], 0.06)

    def test_process_failure_is_reported_and_not_resumed(self):
        result = self.run_session(FAKE_MODE="error")
        event = json.loads(result.stdout)
        self.assertEqual(event["rc"], 17)
        self.assertTrue(event["is_error"])
        self.assertEqual(event["user_turns"], 1)
        self.assertEqual(event["error"], "agent failed")

    def test_malformed_adapter_output_is_an_error(self):
        result = self.run_session(FAKE_MODE="malformed")
        event = json.loads(result.stdout)
        self.assertNotEqual(event["rc"], 0)
        self.assertTrue(event["is_error"])
        self.assertIn("invalid result", event["error"])

    def test_timeout_is_enforced_by_shared_runner(self):
        result = self.run_session(FAKE_MODE="timeout", SESSION_TIMEOUT_S="1")
        event = json.loads(result.stdout)
        # GNU timeout reports 137 when its bounded TERM grace escalates to group KILL.
        self.assertIn(event["rc"], (124, 137))
        self.assertTrue(event["is_error"])
        self.assertEqual(event["user_turns"], 1)

    def test_loop_skips_session_and_backs_off_when_reseed_fails(self):
        self.executable(self.bin / "dev-reseed", "echo reseed >>\"$AGENT_STATE_DIR/ops\"; exit 12\n")
        self.executable(self.bin / "dev-session", "echo session >>\"$AGENT_STATE_DIR/ops\"\n")
        # Staggering is the first sleep. Stop at the first subsequent wait so this test observes
        # the real loop's failure branch without waiting for or starting another iteration.
        self.executable(self.bin / "sleep", r'''
if [[ ! -e "$AGENT_STATE_DIR/staggered" ]]; then
  touch "$AGENT_STATE_DIR/staggered"; exit 0
fi
printf '%s\n' "$1" >"$AGENT_STATE_DIR/backoff"
exit 77
''')
        result = subprocess.run([BASH, str(ROOT / "bin/dev-loop")],
                                env=self.env | {"TRAFFIC_ENABLED": "true"},
                                text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 77, result.stderr)
        self.assertEqual((self.home / "state/ops").read_text().splitlines(), ["ready", "reseed"])
        self.assertEqual((self.home / "state/backoff").read_text().strip(), "60")
        self.assertIn("config reset failed", result.stderr)

    def test_non_claude_entrypoint_uses_only_selected_setup(self):
        self.executable(self.bin / "agento11y", "echo agento11y-1.0.0\n")
        entry_env = self.env | {"DEVELOPER_NAME": "fixture", "CLAUDE_CONFIG_DIR": str(self.home / "wrong-claude")}
        entry_env.pop("AGENT_STATE_DIR")
        result = subprocess.run([BASH, str(ROOT / "entrypoint.sh"), BASH, "-c", "printf ready"],
                                env=entry_env,
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "ready")
        self.assertEqual((self.home / ".local/state/agent-host/ops").read_text().splitlines(), ["setup", "reseed"])
        self.assertFalse((self.home / "wrong-claude").exists())

    def test_claude_adapter_keeps_resume_and_cumulative_cost(self):
        self.executable(self.bin / "claude", r'''
[[ "$*" == *'--max-budget-usd '* ]] || exit 71
n=$(cat "$AGENT_STATE_DIR/calls" 2>/dev/null || echo 0)
n=$((n+1)); echo "$n" >"$AGENT_STATE_DIR/calls"
if [[ "$n" == 2 && "$*" != *'--resume claude-resume'* ]]; then exit 72; fi
jq -cn --argjson n "$n" '{session_id:"claude-resume",total_cost_usd:($n*0.03),num_turns:$n,is_error:false}'
''')
        result = self.run_session(DEVELOPER_AGENT="claude-code", AGENT_ADAPTERS_DIR=str(ROOT / "agents"))
        self.assertEqual(result.returncode, 0, result.stderr)
        event = json.loads(result.stdout)
        self.assertEqual(event["agent"], "claude-code")
        self.assertEqual(event["user_turns"], 2)
        self.assertAlmostEqual(event["cost_usd"], 0.06)
        self.assertEqual(event["session_id"], "claude-resume")

    def test_claude_timeout_stops_agent_child(self):
        # The actual Claude adapter must stay in the shared timeout group. A nested timeout
        # otherwise leaves paid inference alive after the conversation was abandoned.
        self.executable(self.bin / "claude", f'''
exec {sys.executable} -c 'import os,signal,time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); Path(os.environ["AGENT_STATE_DIR"], "agent.pid").write_text(str(os.getpid())); time.sleep(20)'
''')
        pid_file = self.home / "state/agent.pid"
        try:
            result = self.run_session(DEVELOPER_AGENT="claude-code", AGENT_ADAPTERS_DIR=str(ROOT / "agents"),
                                      SESSION_TIMEOUT_S="1")
            event = json.loads(result.stdout)
            self.assertIn(event["rc"], (124, 137))
            self.assertTrue(event["is_error"])
            pid = int(pid_file.read_text())
            process = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)],
                                     text=True, capture_output=True, timeout=2)
            # A killed child can briefly be a zombie while the OS reaps it; it cannot execute.
            self.assertTrue(not process.stdout.strip() or process.stdout.strip().startswith("Z"),
                            f"agent child {pid} still running: {process.stdout}")
        finally:
            if pid_file.exists():
                try:
                    os.kill(int(pid_file.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_unknown_adapter_fails_before_seed(self):
        result = self.run_session(DEVELOPER_AGENT="missing")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("adapter 'missing' is not installed", result.stderr)
        self.assertFalse((self.home / "state/calls").exists())

    def test_seed_failure_has_agent(self):
        self.executable(self.home / "seed", "exit 1\n")
        result = self.run_session()
        self.assertEqual(result.returncode, 3)
        event = json.loads(result.stdout)
        self.assertEqual(event["agent"], "fake")
        self.assertEqual(event["error"], "codebase seed failed")


if __name__ == "__main__":
    unittest.main()
