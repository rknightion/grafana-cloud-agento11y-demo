#!/usr/bin/env bash
# Developer container start: prepare the selected agent, reset its config and run traffic.
set -Eeuo pipefail

log() { printf '%s dev-entrypoint[%s]: %s\n' "$(date -u +%FT%TZ)" "${DEVELOPER_NAME:-?}" "$*" >&2; }

runtime_lib="${DEV_RUNTIME_LIB:-/usr/local/lib/dev-workstation/agent-runtime.sh}"
if [[ ! -r "$runtime_lib" ]]; then
  runtime_lib="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/lib/agent-runtime.sh"
fi
# shellcheck source=apps/dev-workstation/lib/agent-runtime.sh
source "$runtime_lib"

: "${DEVELOPER_NAME:?}"
"$AGENT_ADAPTER" setup

# Agent Observability CLI: the image ships a pinned build; a specific agento11y_cli_version
#    that differs is installed into ~/.local/bin (the installer verifies the archive checksum).
want="${AGENTO11Y_CLI_VERSION:-latest}"
have="$(agento11y --version 2>/dev/null | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
if [[ "$want" != "latest" && -n "$want" && "$want" != "$have" ]]; then
  log "installing agento11y $want (image has ${have:-none})"
  VERSION="$want" INSTALL_DIR="$HOME/.local/bin" sh /usr/local/lib/agento11y-install.sh >&2 \
    || log "agento11y $want install failed; keeping ${have:-none}"
fi
log "agento11y $(agento11y --version 2>/dev/null | head -1)"

# Reset the selected agent's configuration to the known state on every start.
dev-reseed

if [[ $# -gt 0 ]]; then
  exec "$@"
fi
exec dev-loop
