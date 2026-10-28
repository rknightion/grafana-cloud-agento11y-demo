# Claude apps gateway runtime. The image carries NO Claude Code binary: the entrypoint downloads the
# pinned release for the container's architecture at start and verifies it against Anthropic's
# GPG-signed release manifest (see claude-install.sh). Build context: apps/gateway.
# Base images are pinned by tag and multi-arch index digest; bump both together.

FROM debian:bookworm-slim@sha256:99c0b25c46d0214d5a2091092e7908907dcaecd6a962cde0ac700acee222b6f3 AS release-key
# Anthropic's Claude Code release signing key, fetched at build time and refused unless its
# fingerprint matches the one published in the Claude Code setup docs.
ARG RELEASE_SIGNER_URL=https://downloads.claude.ai/keys/claude-code.asc
ARG RELEASE_SIGNER_FPR=31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && rm -rf /var/lib/apt/lists/*
RUN set -eu; \
    curl -fsSL "$RELEASE_SIGNER_URL" -o /tmp/key.asc; \
    fpr="$(gpg --show-keys --with-colons /tmp/key.asc | awk -F: '$1 == "fpr" { print $10; exit }')"; \
    [ "$fpr" = "$RELEASE_SIGNER_FPR" ] || { echo "release key fingerprint $fpr != $RELEASE_SIGNER_FPR" >&2; exit 1; }; \
    gpg --dearmor < /tmp/key.asc > /claude-code-release.gpg

FROM debian:bookworm-slim@sha256:99c0b25c46d0214d5a2091092e7908907dcaecd6a962cde0ac700acee222b6f3
# Install current security fixes for base packages as well as the runtime dependencies.
# Minimum Bookworm jq security update; changing it invalidates cached vulnerable apt layers.
ARG JQ_MIN_VERSION=1.6-2.1+deb12u3
# Bookworm security floors for packages pulled in as dependencies (checked only when installed).
ARG APT_SECURITY_FLOORS="libexpat1:2.5.0-1+deb12u5 libbrotli1:1.0.9-2+deb12u1"
# hadolint ignore=DL3005,DL3008
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends ca-certificates curl gpgv jq libjq1 tini \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' jq)" ge "$JQ_MIN_VERSION" \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' libjq1)" ge "$JQ_MIN_VERSION" \
    && for floor in $APT_SECURITY_FLOORS; do \
         v="$(dpkg-query -W -f='${Version}' "${floor%%:*}" 2>/dev/null || true)"; \
         [ -z "$v" ] || dpkg --compare-versions "$v" ge "${floor#*:}" \
           || { echo "${floor%%:*} $v is below ${floor#*:}" >&2; exit 1; }; \
       done \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 gateway \
    && useradd --uid 10001 --gid 10001 --home-dir /home/gateway --create-home --shell /usr/sbin/nologin gateway \
    && install -d -o 10001 -g 10001 /opt/claude-code

COPY --from=release-key /claude-code-release.gpg /usr/share/keyrings/claude-code-release.gpg
COPY claude-install.sh /usr/local/bin/claude-install
COPY entrypoint.sh /usr/local/bin/gateway-entrypoint

ENV HOME=/home/gateway \
    CLAUDE_CONFIG_DIR=/tmp/.claude \
    CLAUDE_CODE_CACHE=/opt/claude-code \
    DISABLE_AUTOUPDATER=1

USER 10001:10001
EXPOSE 443
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/gateway-entrypoint"]
