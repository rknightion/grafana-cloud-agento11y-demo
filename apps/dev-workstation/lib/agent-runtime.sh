#!/usr/bin/env bash
# Shared adapter discovery. Unknown agents must fail before a session or gateway login.
DEV_RUNTIME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DEVELOPER_AGENT="${DEVELOPER_AGENT:-claude-code}"
if [[ ! "$DEVELOPER_AGENT" =~ ^[a-z][a-z0-9-]*$ ]]; then
  printf "developer agent: invalid agent name '%s'\n" "$DEVELOPER_AGENT" >&2
  exit 2
fi
adapters_dir="${AGENT_ADAPTERS_DIR:-$DEV_RUNTIME_DIR/agents}"
if [[ -z "${AGENT_ADAPTERS_DIR:-}" && ! -d "$adapters_dir" ]]; then
  adapters_dir="$DEV_RUNTIME_DIR/../agents"
fi
AGENT_ADAPTER="$adapters_dir/$DEVELOPER_AGENT/adapter"
if [[ ! -x "$AGENT_ADAPTER" ]]; then
  printf "developer agent: adapter '%s' is not installed (%s)\n" "$DEVELOPER_AGENT" "$AGENT_ADAPTER" >&2
  exit 2
fi
if [[ "$DEVELOPER_AGENT" == claude-code ]]; then
  export AGENT_STATE_DIR="${AGENT_STATE_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}/agent-host}"
else
  export AGENT_STATE_DIR="${AGENT_STATE_DIR:-$HOME/.local/state/agent-host}"
fi
mkdir -p "$AGENT_STATE_DIR"
