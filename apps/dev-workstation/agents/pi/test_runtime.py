"""Exercise the shipped adapter's rendered file and real CLI configuration boundary."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pi-rendered-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.config = self.home / "rendered.json"
        self.config.write_text(json.dumps({"provider": "amazon-bedrock", "region": "eu-west-2",
            "model": {"id": "profile-route", "name": "claude-haiku-4-5", "contextWindow": 200000,
                      "maxTokens": 4096, "cost": {"input": 1.1, "output": 5.5, "cacheRead": 0.11, "cacheWrite": 1.375}}}))
        self.credentials = self.home / "credentials"
        self.credentials.write_text("[default]\naws_access_key_id = fixture\naws_secret_access_key = fixture-secret\n")
        self.credentials.chmod(0o600)
        config = self.home / ".config/agento11y"
        config.mkdir(parents=True)
        (config / "config.env").write_text("AGENTO11Y_AGENT_NAME=pi/test\n")
        self.env = {**os.environ, "HOME": str(self.home), "DEVELOPER_AGENT_CONFIG_FILE": str(self.config),
                    "AWS_SHARED_CREDENTIALS_FILE": str(self.credentials), "PI_INSTALL_DIR": str(HERE),
                    "MCP_SERVER_NAME": "fixture"}

    def adapter(self, operation):
        return subprocess.run([str(HERE / "adapter"), operation], env=self.env,
                              capture_output=True, text=True, timeout=5)

    @unittest.skipUnless((HERE / "node_modules").is_dir(), "npm ci required for real CLI configuration")
    def test_reseed_models_are_accepted_by_the_real_cli(self):
        result = self.adapter("setup")
        self.assertEqual(result.returncode, 0, result.stderr)
        agent = self.home / ".pi/agent"
        agent.mkdir(parents=True)
        (agent / "SYSTEM.md").write_text("stale session instruction")
        result = self.adapter("reseed")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((agent / "SYSTEM.md").exists())
        self.assertEqual(next((agent / "backups").rglob("SYSTEM.md")).read_text(), "stale session instruction")
        servers = json.loads((agent / "mcp.json").read_text())["mcpServers"]
        self.assertEqual(set(servers), {"fixture", "time", "fetch", "git", "sequential-thinking", "memory"})
        self.assertTrue(all(server["exposure"] == "direct" for server in servers.values()))
        self.assertEqual(json.loads((agent / "auth.json").read_text()), {})
        # Listing models parses Pi's actual registry without calling Bedrock or MCP.
        result = subprocess.run(["node", str(HERE / "node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js"),
                                 "--list-models", "profile-route"], stdin=subprocess.DEVNULL,
                                env={**self.env, "PI_CODING_AGENT_DIR": str(agent), "AWS_PROFILE": "default",
                                     "PI_OFFLINE": "1", "PI_TELEMETRY": "0", "PI_SKIP_VERSION_CHECK": "1"},
                                cwd=self.home, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("profile-route", result.stdout)
        self.assertNotIn("Error", result.stderr)

    def test_credential_permissions_fail_closed(self):
        self.credentials.chmod(0o644)
        result = self.adapter("ready")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no group/other access", result.stderr)

    def test_invalid_or_free_price_fails_before_reseed(self):
        config = json.loads(self.config.read_text())
        config["model"]["cost"]["output"] = 0
        self.config.write_text(json.dumps(config))
        result = self.adapter("reseed")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("prices must be positive", result.stderr)
        self.assertFalse((self.home / ".pi/agent/models.json").exists())


if __name__ == "__main__":
    unittest.main()
