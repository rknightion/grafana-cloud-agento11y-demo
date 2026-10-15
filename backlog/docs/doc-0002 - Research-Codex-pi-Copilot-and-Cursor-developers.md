---
id: doc-0002
title: 'Research: Codex, pi, Copilot and Cursor developers'
type: specification
created_date: '2026-10-14 11:57'
updated_date: '2026-10-15 17:44'
---
# Research: Codex, pi, Copilot and Cursor developers on the agent host

Research done 2026-10-14 against agento11y `plugins/agento11y/v0.49.0` (the version this demo pins), Codex `rust-v0.162.1`, pi 1.2.0 with `@grafana/agento11y-pi` 0.25.0, Copilot CLI v1.0.97 and Cursor CLI 2026.10.14-0f9edde. Items marked UNVERIFIED need a spike. Re-check anything version-sensitive before relying on it.

## Canonical sources

- Grafana: [Instrument coding agents](https://grafana.com/docs/grafana-cloud/observe-and-act/agent-observability/guides/instrument-coding-agents/). It defers per-agent detail to `plugins/<agent>/README.md` in [grafana/agento11y](https://github.com/grafana/agento11y/tree/main/plugins). These two are authoritative over inference from plugin source.
- From the Grafana guide:
  - Non-interactive setup means writing `~/.config/agento11y/config.env`, or running `agento11y login --endpoint --tenant --token-stdin --otlp-endpoint`.
  - `agento11y <agent> install --json` exists for claude, copilot, opencode and pi, and `agento11y agents reconcile` registers several at once.
  - Codex is excluded from that managed install because it needs a one-time hook trust step.
- The app has a built-in **Coding agents** view: sessions, cost, tokens and tools, by agent, user, repo and branch. Suffixed names such as `claude-code/x` roll up under the base agent.

## Decisions taken (maintainer, 2026-10-14)

1. Scope: Codex and pi are implemented now. Copilot and Cursor are gated behind a go/no-go spike that the maintainer signs off.
2. Model access: a scoped Bedrock credential (new IAM principal) in the agent-host secret.
   - No loop budgets, no AWS Budgets alarm and no data-residency constraint: this is a demo environment.
   - Neither agent can use the Claude apps gateway: it has no unattended auth and serves only Anthropic Messages.
   - Developer containers cannot reach IMDS, and that stays true.
3. Hosting: same agent host. All `render.py` and seam changes land together, with one planned host replacement at release.

## Cross-cutting facts

- **Host replacement.** `agent-host/render/render.py`, `agent-host/host/*` and `agent-host/config/*` are in the root-run bundle, and their SHA-256s are in user_data. Editing any of them, or bumping `images.tag`, replaces the EC2 host. That resets the gateway Postgres ledger and forces Claude developers to sign in again. The new knobs and the developer list live in the secret's `config` key and do not replace the host.
- **No gateway env push.** For non-Claude developers, the `AGENTO11Y_*` env that `gateway_config` sends Claude Code today must come from the container. Write `~/.config/agento11y/config.env`; Codex hooks run with a stripped environment, so the file is required there.
- **Agent name.** The plugin READMEs say not to put a `/` in a non-Claude agent name, because a slash marks a subagent. Guard calls carry no tags, so rules can scope to the demo only by agent name.
  - Trade-off: a demo-scoped name such as `codex-touchline` shows as its own row in the Coding agents view.
  - Codex suggests `codex-<prefix>`. The pi spike used `pi/touchline` successfully.
  - Pick one convention for all new agents.
- **Auto coding-agent tags.** Sessions run in `mktemp -d` checkouts with no `origin`, so `repo` and `branch` would be unbounded label values. Set static `AGENTO11Y_TAGS` (`service.namespace`, `team`), and enable `user` at most.
- **Tool-name vocabulary.** The guard rules in `terraform/grafana-agento11y.tf` use Claude names (`Bash(...)`, `Read(...)`, `Edit(...)`, `Write(...)`, `Grep(...)`, `WebFetch`). New agents differ, and case-sensitivity of `blocked_tools` matching is UNVERIFIED.
- **Dashboards.** `terraform/dashboards/claude-code.json.tftpl` and the alert and recording rules are built on Claude Code's native `claude_code_*` metrics. None of the new agents emit those. The built-in Coding agents view is the first-cut surface; per-agent dashboards are optional follow-ups.
- **Dev session scripts are Claude-specific.** `apps/dev-workstation/bin/dev-session` uses `claude -p`, `--allowedTools`, `total_cost_usd`, `permission_denials` and a `blocked by hook` grep. The prompt corpus is agent-neutral, and its picking, follow-up, abandon and PII-burst logic can be shared.

## Codex

- **Plugin.**
  - `plugins/codex` v0.5.0 is experimental and hook-based (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop).
  - It emits one generation per turn, not one per model call; intermediate assistant text and reasoning text are lost.
  - Tokens are read from the rollout JSONL, so never use `codex exec --ephemeral`.
  - Preflight deny works (UserPromptSubmit), and so do postflight deny and redaction (PreToolUse with `updatedInput`).
  - Hooks cover `Bash`, `apply_patch` (matcher aliases `Edit` and `Write`) and `mcp__server__tool`. Hosted tools such as WebSearch are not hooked.
- **Hook trust headless (preferred route).**
  - Define the five hooks inline in the root-owned system layer `/etc/codex/config.toml`, baked into the image. System-layer hooks are "managed" and trusted by policy.
  - Mirror `plugins/codex/hooks/hooks.json` at the pinned tag, and add a CI check that the two stay in sync.
  - Fallback: `--dangerously-bypass-hook-trust` on every `codex exec` and `codex exec resume`.
  - Both UNVERIFIED in `codex exec`.
- **Headless.**
  - `codex exec --json` returns JSONL with `thread.started` and `turn.completed` (usage); follow-ups use `codex exec resume <id>`.
  - Codex's own sandbox likely fails under `cap_drop: ALL`, so run `--sandbox danger-full-access` inside the isolated container.
  - No login bot.
- **Model.**
  - Use the built-in `amazon-bedrock` provider, with OpenAI models (`openai.gpt-5.6-luna`, `-terra`, `-sol`, `openai.gpt-5.5`) on `bedrock-mantle`, authenticated by `AWS_BEARER_TOKEN_BEDROCK` or SigV4 keys.
  - Mantle availability may be US regions only, and a US region is acceptable.
  - Application inference profiles are not supported on mantle.
  - IAM action: `bedrock-mantle:CreateInference`.
  - The OpenAI help article warns that MCP namespace tools and tool search are limited on Bedrock, and 14 of 53 prompts touch MCP.
  - `mapperutil.InferProvider` does not recognise the `openai.` prefix, so the provider falls back to `codex` and cost may be missing. A small upstream fix is possible.
- **Native OTel.**
  - `[otel]` in `config.toml`, OTLP/HTTP with a literal Basic auth header. The seed `config.toml` is rendered from a secret file.
  - Metrics include `codex.turn.token_usage`, `codex.turn.cost_microusd` and `codex.tool.call`; Prometheus names are UNVERIFIED.
  - Codex logs need `logs:write`, which `agento11y_client_token` lacks. Use a separate scoped token, because the ingest token must never enter a developer container.
  - Set `analytics.enabled=false`, `check_for_update_on_startup=false` and cumulative temporality.
- **Install.** Pinned `codex-package-<arch>-unknown-linux-musl.tar.gz` from the release, plus `SHA256SUMS` and a sigstore bundle. It is Apache-2.0, so it can be baked into the image.
- **Sources:**
  - https://learn.chatgpt.com/docs/non-interactive-mode
  - https://learn.chatgpt.com/docs/hooks
  - https://help.openai.com/en/articles/20001253-configure-codex-with-amazon-bedrock
  - https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html
  - https://github.com/openai/codex/tree/main/codex-rs/otel

## pi

- **Upstream.** pi moved to `earendil-works/pi`, and npm moved to `@earendil-works/*`. Since 0.99.0 it has built-in MCP (stdio and streamable HTTP, `~/.pi/agent/mcp.json`); set `"exposure": "direct"` so tools appear as `mcp__server__tool`.
- **Plugin.**
  - `@grafana/agento11y-pi` is an in-process extension loaded with `pi -e <dir>`. It emits one generation per turn, with tokens, cost from pi's own price catalog, content, tags and tool spans.
  - Verified in a local spike on pi 1.2.0: print and JSON modes load it, generations export, and a postflight deny blocks `bash`.
  - Preflight deny does not stop the model call (a documented gap, grafana/agento11y#861). Preflight transform and redaction does work, on every model call.
  - Reasoning tokens are dropped (#825).
  - The plugin is tested upstream against pi 0.87.1. Pin both pi and the plugin, and re-spike on every bump.
- **Headless.**
  - Run `pi --mode json ... </dev/null`; it hangs if stdin is left open. Follow-ups reuse `--session-id`.
  - Set `PI_TELEMETRY=0`, `PI_OFFLINE=1` and `PI_SKIP_VERSION_CHECK=1`.
  - No permission system, so `bash` is unrestricted and only the container isolation and the guards bound it.
  - No login.
- **Model.**
  - Direct Bedrock with the scoped key, against the existing per-team application inference profiles (`data.aws_iam_policy_document.bedrock_invoke`).
  - For custom ARN model ids, `models.json` needs explicit `cost`, or `cost_usd` is 0. Whether pi routes profile ARNs correctly is UNVERIFIED.
- **Install.** Lockfile-pinned `npm ci --ignore-scripts` in the image, before the step that removes npm. Do not use `agento11y pi install --json`, which installs the plugin unpinned.
- **Guards.** The hook sends `agent_name` as configured and lowercase tool names (`bash`, `{"command": ...}`).
- **Sources:**
  - https://github.com/earendil-works/pi (`packages/coding-agent/docs/`)
  - https://pi.dev/news/2026/5/7/pi-has-a-new-home
  - `plugins/pi/README.md`

## Copilot (gated)

- **Surface.** Copilot CLI (`copilot`). The plugin is hook-based; `agento11y copilot install --json` writes `~/.copilot/hooks/agento11y.json`.
- **Plugin.**
  - One generation per turn at `agentStop`, read from `~/.copilot/session-state/<id>/events.jsonl`. Token data may be partial.
  - **No preflight guards.** Postflight deny works, and redaction works on the CLI surface.
  - `AGENTO11Y_USER_ID` is required.
- **Headless.**
  - Run `copilot -p --no-ask-user --allow-tool/--deny-tool --output-format json` with `COPILOT_GITHUB_TOKEN`.
  - The token can be a fine-grained PAT with the Copilot Requests permission, owned by a personal account. Classic PATs are not supported.
  - No login bot.
  - UNVERIFIED: whether hooks fire in `-p` mode, and whether `-p` can resume a session.
- **Model.**
  - GitHub-hosted only, which needs Copilot seat(s) billed in GitHub AI Credits, with overage on by default.
  - BYOK supports `openai`, `azure` and `anthropic` provider types, but not Bedrock.
- **Native OTel.** `COPILOT_OTEL_ENABLED`, OTLP/HTTP, GenAI semantic conventions; no cost attribute.
- **Blockers needing the maintainer.**
  - The identity model: one shared identity or one per persona.
  - Seats.
  - Whether a 24/7 synthetic loop is acceptable under GitHub's terms and abuse detection; no official statement was found.
- **Sources:**
  - https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference
  - https://docs.github.com/en/copilot/reference/hooks-reference
  - https://docs.github.com/en/copilot/concepts/agents/opentelemetry
  - `plugins/copilot/README.md`

## Cursor (gated)

- **Surface.** `cursor-agent` CLI, which works on Linux arm64. The plugin is hook-based (`agento11y cursor install` writes `~/.cursor/hooks.json`) and is written for the IDE first.
- **Blocker.** In headless `agent -p` mode Cursor does not emit `beforeSubmitPrompt`, `afterAgentResponse` or `stop` (per Cursor staff, 2026-08). The result has no prompt, assistant text or tokens, no preflight guard, and `generation_id == conversation_id`. A Linux arm64 report also has hooks failing silently.
  - Workarounds:
    - accept capture limited to tool spans;
    - evaluate a wrapper over `--output-format stream-json` that emits generations via the agento11y SDK; token usage remains UNVERIFIED because the current official output schema does not document it;
    - wait for Cursor to fix it.
- **Model.** Always Cursor's hosted backend, which needs paid Cursor seat(s) or Enterprise service accounts. Bedrock BYOK is documented for the IDE only. No per-session budget.
- **Install.** A tarball from `downloads.cursor.com` with no published checksum or signature. Redistribution terms are unknown, so install at container start rather than baking it into the public image.
- **Sources:**
  - https://cursor.com/docs/cli/headless
  - https://cursor.com/docs/hooks
  - https://forum.cursor.com/t/cursor-cli-omits-beforesubmitprompt-afteragentresponse-and-stop-hooks-loses-token-usage-and-emits-inconsistent-generation-id-values/169059
  - `plugins/cursor/README.md`


## Maintainer decisions and refresh, 2026-10-15

- Keep the existing demo stack destination.
- Copilot: use the existing seat for a bounded spike only; continuous synthetic traffic requires a separate decision after results.
- Cursor: defer deployment. Resume after a pinned headless release proves the required lifecycle and token fields, or an explicit decision accepts incomplete capture. Current [output-format documentation](https://cursor.com/docs/cli/reference/output-format) does not establish token usage; the earlier stream-json usage claim was unverified.
- SDK JS 0.13.0 and CLI/plugin 0.49.0 remain the latest stable releases, verified against GitHub releases and npm. Retain pins; use `agento11y doctor --require-cloud` for live validation. CLI 0.49.0 anonymous statistics are disabled explicitly in the demo image.
