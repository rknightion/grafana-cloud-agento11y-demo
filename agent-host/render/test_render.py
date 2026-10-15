#!/usr/bin/env python3
"""Exercise the shipped renderer CLI with synthetic credentials and a mixed roster."""
import configparser
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

import yaml

HERE = Path(__file__).resolve().parent


def inputs():
    host = dict(name="touchline", aws_region="eu-west-1", images_registry="registry.example",
                images_name_prefix="demo-", images_tag="test")
    dev = dict(name="alex.morgan", email="alex.morgan@touchline.example", team="newsroom", sub="fake-sub")
    config = dict(codex_bedrock={"model": "openai.gpt-5.6-luna", "region": "us-east-1"}, gateway_hostname="touchline-gateway.internal", claude_code_version="2.1.104",
                  agento11y_cli_version="latest", developers=[dev], teams=["newsroom"],
                  spend_caps={"users": {dev["name"]: {"daily": 1}}},
                  gateway_models=[dict(key="haiku", id="claude-haiku-4-5", upstream_profile_arn="fake-profile", upstream_profile_arns_by_team={"newsroom": "fake-newsroom-profile"}, source_profile="eu.anthropic.claude-haiku-4-5-20251001-v1:0")],
                  team_model_allowlist={}, cognito_issuer="https://identity.example", cognito_client_id="fake-client",
                  cognito_domain_url="https://identity.example", traffic_enabled=True, session_interval_minutes=30,
                  content_capture=True, grafana_otlp_endpoint="https://otlp.example", grafana_otlp_username="fake-tenant",
                  agento11y_endpoint="https://agento11y.example", agento11y_tenant="fake-tenant", pdc_cluster="fake-cluster",
                  pdc_hosted_grafana_id="fake-stack", service_names={"agent_host": "touchline-agent-host", "gateway": "touchline-gateway"})
    keys = ("cognito_client_secret gateway_jwt_secret gateway_admin_write_key gateway_admin_read_key "
            "postgres_password postgres_grafana_ro_password grafana_otlp_token agento11y_client_token "
            "pdc_token tls_ca_pem tls_cert_pem tls_key_pem codex_otlp_token").split()
    secret = {key: "synthetic-" + key for key in keys}
    secret.update(config=config, developer_passwords={dev["name"]: "synthetic-developer-password"},
                  developer_bedrock_credentials={agent: {"access_key_id": "synthetic-" + agent + "-key",
                                                         "secret_access_key": "synthetic-" + agent + "-secret",
                                                         "region": "us-east-1" if agent == "codex" else "eu-west-1"}
                                                 for agent in ("codex", "pi")})
    return host, secret


def render(root, host, secret, script=HERE / "render.py"):
    root.mkdir(parents=True, exist_ok=True)
    (root / "host.json").write_text(json.dumps(host))
    # Fixed pre-existing password models a real re-render without random golden output.
    su = root / "out/secrets/postgres/superuser_password"
    su.parent.mkdir(parents=True, exist_ok=True)
    su.write_text("synthetic-persisted-superuser")
    result = subprocess.run([sys.executable, str(script), "--vars", str(root / "host.json"),
                             "--out", str(root / "out"), "--secret-stdin", "--check"],
                            input=json.dumps(secret), text=True, capture_output=True, timeout=15)
    return result, root / "out"


class RendererCliTests(unittest.TestCase):
    def test_legacy_and_explicit_claude_are_byte_identical(self):
        """Optional agent defaults must preserve the existing host's compose and gateway bytes."""
        host, secret = inputs()
        expected = json.loads((HERE / "claude-baseline.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            for explicit in (False, True):
                if explicit:
                    secret["config"]["developers"][0]["agent"] = "claude-code"
                result, out = render(Path(temp) / str(explicit), host, secret)
                self.assertEqual(result.returncode, 0, result.stderr)
                for filename, digest in expected["sha256"].items():
                    self.assertEqual(hashlib.sha256((out / filename).read_bytes()).hexdigest(), digest, filename)

    def test_mixed_roster_secret_and_mount_isolation(self):
        host, secret = inputs()
        for agent in ("codex", "pi"):
            secret["config"]["developers"].append(dict(name=agent + ".dev", email=agent + "@touchline.example", team="newsroom", agent=agent))
            secret["config"]["spend_caps"]["users"][agent + ".dev"] = {"daily": 9}
        with tempfile.TemporaryDirectory() as temp:
            result, out = render(Path(temp), host, secret)
            self.assertEqual(result.returncode, 0, result.stderr)
            project = yaml.safe_load((out / "compose.yaml").read_text())
            for agent in ("codex", "pi"):
                service = project["services"][f"dev-{agent}-dev"]
                env = service["environment"]
                self.assertEqual(env["DEVELOPER_AGENT"], agent)
                self.assertEqual(env["HOME"], "/home/node")
                self.assertEqual(env["AGENT_STATE_DIR"], "/home/node/.local/state/agent-host")
                self.assertEqual(env["NODE_EXTRA_CA_CERTS"], "")
                self.assertNotIn("depends_on", service)
                self.assertFalse(any("claude" in mount or "ca.pem" in mount or "gateway-cert" in mount for mount in service["volumes"]))
                self.assertIn(f"{agent}-home-{agent}-dev:/home/node", service["volumes"])
                self.assertEqual(len(service["secrets"]), 3 if agent == "pi" else 4)
                self.assertEqual(env["AWS_SHARED_CREDENTIALS_FILE"], "/run/secrets/developer_aws_credentials")
                self.assertEqual(env["AWS_EC2_METADATA_DISABLED"], "true")
                self.assertEqual(env["AWS_REGION"], "us-east-1" if agent == "codex" else "eu-west-1")
                expected_model = "openai.gpt-5.6-luna" if agent == "codex" else "fake-newsroom-profile"
                self.assertEqual(env["SESSION_MODELS"], expected_model + "=1")
                by_target = {entry["target"]: entry for entry in service["secrets"]}
                aws_ref = by_target["/run/secrets/developer_aws_credentials"]
                aws_file = out / project["secrets"][aws_ref["source"]]["file"].removeprefix("/etc/agent-host/")
                self.assertEqual(stat.S_IMODE(aws_file.stat().st_mode), 0o400)
                credentials = configparser.ConfigParser()
                credentials.read(aws_file)
                self.assertEqual(credentials["default"]["aws_access_key_id"], f"synthetic-{agent}-key")
                self.assertEqual(credentials["default"]["aws_secret_access_key"], f"synthetic-{agent}-secret")
                if agent == "pi":
                    pi_ref = by_target["/run/pi/config.json"]
                    pi_file = out / project["secrets"][pi_ref["source"]]["file"].removeprefix("/etc/agent-host/")
                    self.assertEqual(stat.S_IMODE(pi_file.stat().st_mode), 0o400)
                    pi_config = json.loads(pi_file.read_text())
                    self.assertEqual(pi_config["model"]["id"], "fake-newsroom-profile")
                    self.assertEqual(pi_config["provider"], "amazon-bedrock")
                    self.assertEqual(pi_config["model"]["cost"], dict(input=1.1, output=5.5, cacheRead=0.11, cacheWrite=1.375))
                if agent == "codex":
                    codex_ref = by_target["/run/codex/config.json"]
                    codex_file = out / project["secrets"][codex_ref["source"]]["file"].removeprefix("/etc/agent-host/")
                    self.assertEqual(stat.S_IMODE(codex_file.stat().st_mode), 0o400)
                    codex_config = json.loads(codex_file.read_text())
                    self.assertEqual(codex_config, {"provider": "amazon-bedrock", "region": "us-east-1",
                                                  "model": {"id": "openai.gpt-5.6-luna", "cost": {"input": 0.22, "output": 1.32,
                                                            "cacheRead": 0.022, "cacheWrite": 0.275}, "contextWindow": 272000},
                                                  "otel": {"endpoint": "https://otlp.example", "username": "fake-tenant"}})
                    token_ref = by_target["/run/secrets/codex_otlp_token"]
                    token_file = out / project["secrets"][token_ref["source"]]["file"].removeprefix("/etc/agent-host/")
                    self.assertEqual(stat.S_IMODE(token_file.stat().st_mode), 0o400)
                    self.assertEqual(token_file.read_text(), "synthetic-codex_otlp_token")
                else:
                    self.assertNotIn("/run/secrets/codex_otlp_token", by_target)
                    self.assertNotIn("/run/codex/config.json", by_target)
                ref = service["secrets"][0]
                self.assertEqual(ref["target"], "/home/node/.config/agento11y/config.env")
                relative = project["secrets"][ref["source"]]["file"].removeprefix("/etc/agent-host/")
                config_file = out / relative
                self.assertEqual(stat.S_IMODE(config_file.stat().st_mode), 0o400)
                content = config_file.read_text()
                for wanted in (f"AGENTO11Y_AGENT_NAME='{agent}-touchline'", f"AGENTO11Y_USER_ID='{agent}@touchline.example'",
                               "AGENTO11Y_TAGS='service.namespace=touchline,team=newsroom'", "synthetic-agento11y_client_token",
                               "AGENTO11Y_AUTO_CODING_AGENT_TAGS='false'"):
                    self.assertIn(wanted, content)
                for forbidden in ("synthetic-grafana_otlp_token", "synthetic-developer-password", "cognito", "gateway_jwt"):
                    self.assertNotIn(forbidden, content)
            for marker in ("synthetic-agento11y_client_token", "synthetic-codex-key", "synthetic-pi-secret", "synthetic-codex_otlp_token"):
                self.assertNotIn(marker, (out / "compose.yaml").read_text())
            native_token_files = [str(path.relative_to(out)) for path in (out / "secrets").rglob("*")
                                  if path.is_file() and "synthetic-codex_otlp_token" in path.read_text()]
            self.assertEqual(native_token_files, ["secrets/dev-codex-dev/codex_otlp_token"])
            self.assertEqual(len(project["services"]["dev-alex-morgan"]["secrets"]), 1)
            caps = json.loads(project["services"]["spend-caps"]["environment"]["SPEND_CAPS"])
            self.assertEqual([cap["scope"]["user_id"] for cap in caps], ["fake-sub"])

    def test_non_claude_only_roster_needs_no_passwords(self):
        host, secret = inputs()
        dev = secret["config"]["developers"][0]
        dev["agent"] = "pi"
        dev.pop("sub")
        secret["developer_passwords"] = {}
        with tempfile.TemporaryDirectory() as temp:
            result, out = render(Path(temp), host, secret)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((out / "secrets/dev-alex-morgan/developer_password").exists())
            self.assertTrue((out / "secrets/dev-alex-morgan/agento11y_config").exists())

    def test_non_claude_missing_credential_and_unpriced_model_fail_closed(self):
        for missing_credentials in (True, False):
            host, secret = inputs()
            secret["config"]["developers"][0]["agent"] = "pi"
            if missing_credentials:
                secret["developer_bedrock_credentials"] = {}
            else:
                secret["config"]["gateway_models"][0]["source_profile"] = "eu.anthropic.claude-sonnet-4-6"
            with tempfile.TemporaryDirectory() as temp:
                result, _ = render(Path(temp), host, secret)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("missing Bedrock credentials" if missing_credentials else "unsupported pi model", result.stderr)

    def test_codex_requires_native_telemetry_token_and_verified_model(self):
        for missing_token in (True, False):
            host, secret = inputs()
            secret["config"]["developers"][0]["agent"] = "codex"
            if missing_token:
                secret.pop("codex_otlp_token")
            else:
                secret["config"]["codex_bedrock"]["model"] = "openai.unverified-model"
            with tempfile.TemporaryDirectory() as temp:
                result, _ = render(Path(temp), host, secret)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("missing Codex OTLP token" if missing_token else "unsupported Codex model", result.stderr)

    def test_unsupported_agent_is_rejected(self):
        host, secret = inputs()
        secret["config"]["developers"][0]["agent"] = "cursor"
        with tempfile.TemporaryDirectory() as temp:
            result, _ = render(Path(temp), host, secret)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported developer agent", result.stderr)


if __name__ == "__main__":
    unittest.main()
