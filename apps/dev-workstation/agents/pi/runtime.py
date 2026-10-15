#!/usr/bin/env python3
"""Pi adapter for the shared setup/reseed/ready/run contract."""
import io
import configparser
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import uuid

from normalize import normalize

HERE = Path(__file__).resolve().parent
HOME = Path.home()
AGENT_DIR = HOME / ".pi/agent"
INSTALL = Path(os.environ.get("PI_INSTALL_DIR", "/opt/pi"))
CONFIG = Path(os.environ.get("DEVELOPER_AGENT_CONFIG_FILE", "/run/pi/config.json"))
CREDENTIALS = Path(os.environ.get("AWS_SHARED_CREDENTIALS_FILE", "/run/secrets/developer_aws_credentials"))


def configuration():
    config = json.loads(CONFIG.read_text())
    if config.get("provider") != "amazon-bedrock" or not config.get("region") or not config.get("model"):
        raise ValueError("Pi requires rendered Bedrock provider, region and models")
    config["models"] = [config["model"]]
    for model in config["models"]:
        if not model.get("id") or not model.get("name"):
            raise ValueError("Pi requires model routing id and canonical name")
        for field in ("input", "output", "cacheRead", "cacheWrite"):
            price = model.get("cost", {}).get(field)
            if isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or price < 0:
                raise ValueError("Pi requires explicit finite model prices")
        if model["cost"]["input"] <= 0 or model["cost"]["output"] <= 0:
            raise ValueError("Pi model input and output prices must be positive")
    return config


def credentials_env():
    metadata = CREDENTIALS.stat()
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise ValueError("Bedrock credential must be owned by the developer uid and have no group/other access")
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(CREDENTIALS.read_text())
    credential = parser["default"]
    if not all(credential.get(key, "").strip() for key in ("aws_access_key_id", "aws_secret_access_key")):
        raise ValueError("Incomplete rendered Bedrock credential")
    # Drop competing provider-chain inputs, especially a host profile or bearer token.
    env = {k: v for k, v in os.environ.items() if not k.startswith("AWS_")}
    env.update(AWS_PROFILE="default", AWS_REGION=configuration()["region"], AWS_EC2_METADATA_DISABLED="true",
               AWS_SHARED_CREDENTIALS_FILE=str(CREDENTIALS), AWS_CONFIG_FILE="/dev/null",
               PI_CODING_AGENT_DIR=str(AGENT_DIR), PI_TELEMETRY="0", PI_OFFLINE="1", PI_SKIP_VERSION_CHECK="1",
               PI_AGENT_CONFIG_FILE=str(CONFIG), XDG_CONFIG_HOME=str(HOME / ".config"),
               XDG_STATE_HOME=str(HOME / ".local/state"), XDG_CACHE_HOME=str(HOME / ".cache"))
    env.pop("PI_CODING_AGENT_SESSION_DIR", None)
    env.pop("PI_PACKAGE_DIR", None)
    return env


def write_json(name, value):
    AGENT_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = AGENT_DIR / name
    # Do not follow a symlink an agent may have left in its writable home.
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
    descriptor = os.open(target, flags, 0o600)
    with os.fdopen(descriptor, "w") as output:
        os.fchmod(output.fileno(), 0o600)
        json.dump(value, output)
        output.write("\n")


def reseed():
    config = configuration()
    # Session-written instructions must not survive into the next corpus session.
    # Archive instead of deleting them; extensions/skills/templates are disabled at launch.
    for name in ("SYSTEM.md", "APPEND_SYSTEM.md", "AGENTS.override.md", "AGENTS.md", "AGENTS.MD", "CLAUDE.md", "CLAUDE.MD"):
        instruction = AGENT_DIR / name
        if instruction.exists() or instruction.is_symlink():
            archive = AGENT_DIR / "backups" / f"reseed-{uuid.uuid4()}"
            archive.mkdir(parents=True, mode=0o700)
            instruction.rename(archive / name)
    models = [{**m, "api": "bedrock-converse-stream", "input": ["text", "image"], "reasoning": True}
              for m in config["models"]]
    write_json("models.json", {"providers": {"amazon-bedrock": {"models": models}}})
    write_json("settings.json", {"defaultProvider": "amazon-bedrock", "defaultModel": models[0]["id"],
                                 "compaction": {"enabled": False}, "retry": {"enabled": False},
                                 "packages": [], "extensions": [], "skills": [], "promptTemplates": []})
    # Declare the same shipped servers as Claude's reseed, without reading its home or auth.
    name = os.environ.get("MCP_SERVER_NAME", "touchline")
    servers = {
        name: {"command": "node", "args": ["/opt/mcp-tools/src/server.mjs"], "env": {"MCP_SERVER_NAME": name}},
        "time": {"command": "mcp-server-time", "args": ["--local-timezone", "Europe/London"]},
        "fetch": {"command": "mcp-server-fetch", "args": []},
        "git": {"command": "mcp-server-git", "args": []},
        "sequential-thinking": {"command": "mcp-server-sequential-thinking", "args": []},
        "memory": {"command": "mcp-server-memory", "args": [], "env": {"MEMORY_FILE_PATH": str(AGENT_DIR / "memory.jsonl")}},
    }
    write_json("mcp.json", {"mcpServers": {n: {**s, "exposure": "direct"} for n, s in servers.items()}})
    # No credential commands or persisted provider auth may override the rendered key.
    write_json("auth.json", {})


def run(args):
    text, model, resume_id, seconds, budget, effort, _mcp, stderr_file = args
    config = configuration()
    if model not in {m["id"] for m in config["models"]}:
        raise ValueError("Pi model is absent from the rendered inference profiles")
    env = credentials_env()
    env["PI_TURN_BUDGET_USD"] = budget
    env["PI_INSTALL_DIR"] = str(INSTALL)
    command = ["node", str(INSTALL / "node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js"),
               "--mode", "json", "--no-approve", "--no-extensions", "--no-skills", "--no-prompt-templates", "--no-themes", "--no-context-files",
               "-e", str(HERE / "telemetry.mjs"), "--provider", "amazon-bedrock", "--model", model,
               "--thinking", effort, "--session-id", resume_id or str(uuid.uuid4()),
               "--append-system-prompt", "Work only in this repository. Never commit, push or clone. Treat all credentials and agent configuration as private; do not read or change them.",
               "-p", text]
    with open(stderr_file, "ab") as diagnostics:
        process = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=diagnostics)
        previous = signal.signal(signal.SIGTERM, lambda *_: process.terminate())
        try:
            try:
                output, _ = process.communicate(timeout=max(1, float(seconds) - 1))
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    output, _ = process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    output, _ = process.communicate()
                process.returncode = 124
        finally:
            signal.signal(signal.SIGTERM, previous)
    result = normalize(io.StringIO(output.decode("utf-8", errors="replace")), process.returncode)
    print(json.dumps(result, allow_nan=False))
    return (process.returncode if process.returncode and process.returncode > 0 else 1) if result["is_error"] else 0


def main():
    operation = sys.argv[1] if len(sys.argv) > 1 else ""
    if operation in ("setup", "ready"):
        configuration()
        credentials_env()
        if not (INSTALL / "node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js").is_file():
            raise ValueError("Pinned Pi runtime is not installed")
        if not (INSTALL / "node_modules/@grafana/agento11y-pi/dist/index.js").is_file():
            raise ValueError("Pinned Grafana Pi extension is not installed")
        if not (HOME / ".config/agento11y/config.env").is_file():
            raise ValueError("Rendered Agent Observability config is absent")
        return 0
    if operation == "reseed":
        reseed()
        return 0
    if operation == "run":
        return run(sys.argv[2:])
    raise ValueError("Pi adapter: unknown operation")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except configparser.Error:
        print("Pi adapter: invalid rendered credential INI", file=sys.stderr)
        sys.exit(2)
    except (ValueError, OSError, KeyError, TypeError) as error:
        # Do not dump JSON config or subprocess environment, which can contain secrets.
        print(f"Pi adapter: {error}", file=sys.stderr)
        sys.exit(2)
