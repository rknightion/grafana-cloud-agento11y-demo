"""Pin Pi JSONL cost semantics at the shipped parser's process boundary."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

HERE = Path(__file__).resolve().parent


def assistant(cost, **fields):
    return {"role": "assistant", "content": [{"type": "text", "text": "hello\u2028world"}],
            "stopReason": "stop", "usage": {"cost": {"total": cost}}, **fields}


class NormalizeTests(unittest.TestCase):
    def parse(self, events):
        return subprocess.run([sys.executable, str(HERE / "normalize.py")],
                              input="".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events),
                              text=True, capture_output=True, timeout=5)

    def test_counts_final_message_once_and_only_current_invocation(self):
        message = assistant(0.025)
        result = self.parse([
            {"type": "session", "id": "same-session"},
            {"type": "message_update", "usage": {"cost": {"total": 99}}},
            {"type": "message_end", "message": message},
            {"type": "turn_end", "message": message},
            {"type": "agent_end", "messages": [message]},
            {"type": "message_end", "message": assistant(0.015)},
            {"type": "agent_settled", "aborted": False},
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        normalized = json.loads(result.stdout)
        self.assertEqual(normalized["cost_mode"], "incremental")
        self.assertAlmostEqual(normalized["total_cost_usd"], 0.04)
        self.assertEqual(normalized["num_turns"], 2)
        self.assertEqual(normalized["session_id"], "same-session")
        self.assertIn("hello\u2028world", normalized["result"])

    def test_incomplete_stream_and_missing_cost_fail_closed(self):
        for tail in ([], [{"type": "agent_settled", "aborted": False}]):
            message = assistant(0.02)
            if tail:
                del message["usage"]
            result = self.parse([{"type": "session", "id": "run"},
                                 {"type": "message_end", "message": message}, *tail])
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(json.loads(result.stdout)["is_error"])

    @unittest.skipUnless((HERE / "node_modules").is_dir(), "npm ci required for the real Pi CLI boundary")
    def test_real_pi_cli_resume_reports_incremental_cost(self):
        with tempfile.TemporaryDirectory(prefix="pi-cli-boundary-") as directory:
            home = Path(directory)
            agent = home / "agent"
            agent.mkdir()
            requests = []

            class Receiver(BaseHTTPRequestHandler):
                def do_POST(self):
                    requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"results": [{"accepted": True}
                        for _ in requests[-1].get("generations", [])]}).encode())

                def log_message(self, *_args):
                    pass

            server = HTTPServer(("127.0.0.1", 0), Receiver)
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            telemetry = home / ".config/agento11y"
            telemetry.mkdir(parents=True)
            (telemetry / "config.env").write_text(
                f"AGENTO11Y_ENDPOINT=http://127.0.0.1:{server.server_port}\n"
                "AGENTO11Y_AGENT_NAME=pi/fixture\nAGENTO11Y_USER_ID=fixture-user\n"
                "AGENTO11Y_TAGS=service.namespace=fixture,team=platform\n"
                "AGENTO11Y_AUTO_CODING_AGENT_TAGS=false\nAGENTO11Y_DEBUG=true\n")
            config = home / "pi.json"
            config.write_text(json.dumps({"model": {"id": "profile-route", "name": "claude-haiku-4-5"}}))
            (agent / "settings.json").write_text(json.dumps({"compaction": {"enabled": False}, "retry": {"enabled": False}}))
            env = {**os.environ, "HOME": directory, "PI_CODING_AGENT_DIR": str(agent),
                   "XDG_CONFIG_HOME": str(home / ".config"), "XDG_STATE_HOME": str(home / ".local/state"),
                   "XDG_CACHE_HOME": str(home / ".cache"),
                   "PI_TELEMETRY": "0", "PI_OFFLINE": "1", "PI_SKIP_VERSION_CHECK": "1",
                   "PI_AGENT_CONFIG_FILE": str(config), "PI_INSTALL_DIR": str(HERE), "PI_TURN_BUDGET_USD": "1"}
            command = ["node", str(HERE / "node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js"),
                       "--mode", "json", "--no-approve", "--no-extensions", "--no-skills", "--no-themes",
                       "--no-prompt-templates", "-e", str(HERE / "fixture-provider.mjs"),
                       "-e", str(HERE / "telemetry.mjs"),
                       "--provider", "fixture", "--model", "profile-route", "--session-id", "same-session", "-p"]
            for prompt in ("first", "followup"):
                completed = subprocess.run([*command, prompt], cwd=directory, env=env, stdin=subprocess.DEVNULL,
                                           text=True, capture_output=True, timeout=20)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertNotIn("Extension error", completed.stderr)
                normalized = subprocess.run([sys.executable, str(HERE / "normalize.py")],
                                            input=completed.stdout, text=True, capture_output=True, timeout=5)
                self.assertEqual(normalized.returncode, 0, completed.stdout + completed.stderr + normalized.stderr)
                result = json.loads(normalized.stdout)
                self.assertEqual(result["session_id"], "same-session")
                self.assertEqual(result["cost_mode"], "incremental")
                self.assertAlmostEqual(result["total_cost_usd"], 0.025)
                self.assertIn("hello\u2028world", result["result"])
                # Normalizing only Grafana's observer must preserve the real provider id.
                messages = [json.loads(line)["message"] for line in completed.stdout.split("\n") if line
                            and json.loads(line).get("type") == "message_end"
                            and json.loads(line).get("message", {}).get("role") == "assistant"]
                self.assertEqual(messages[-1]["model"], "profile-route")
            debug = list(home.rglob("agento11y.log"))
            self.assertEqual(len(requests), 2, completed.stderr + "\n".join(p.read_text() for p in debug))
            generations = [generation for request in requests for generation in request["generations"]]
            self.assertEqual(len(generations), 2)
            self.assertEqual([g["conversation_id"] for g in generations], ["same-session", "same-session"])
            self.assertEqual(generations[1]["parent_generation_ids"], [generations[0]["id"]])
            for generation in generations:
                self.assertEqual(generation["model"]["name"], "claude-haiku-4-5")
                self.assertEqual(generation["metadata"]["agento11y.user.id"], "fixture-user")
                self.assertEqual(generation["tags"]["team"], "platform")
                self.assertEqual(generation["tags"]["service.namespace"], "fixture")
                self.assertAlmostEqual(generation["metadata"]["cost_usd"], 0.025)

    def test_aborted_and_model_failure_are_not_success_even_when_cli_exits_zero(self):
        for message, aborted in ((assistant(0.01), True),
                                 (assistant(0, stopReason="error", errorMessage="unauthorized"), False)):
            result = self.parse([{"type": "session", "id": "run"},
                                 {"type": "message_end", "message": message},
                                 {"type": "agent_settled", "aborted": aborted}])
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(json.loads(result.stdout)["is_error"])


if __name__ == "__main__":
    unittest.main()
