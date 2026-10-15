# Coding agents: the agent host

The coding-agent half of the demo is one EC2 instance playing a small engineering team. It runs
the Claude apps gateway, its Postgres, a PDC agent, a host Alloy and one container per developer,
all under docker compose. Developers default to Claude Code; optional Codex and pi personas use
direct Bedrock credentials and isolated homes. [agent-host/README.md](https://github.com/rknightion/grafana-cloud-agento11y-demo/blob/main/agent-host/README.md) covers the
boot sequence and the files in detail; this page is the operator's view.

![The agent host: five Claude Code containers reach the Claude apps gateway over HTTPS; the gateway keeps spend in Postgres, signs developers in with Cognito, calls Bedrock with its instance role and forwards telemetry, the plugin sends generations to Agent Observability and the PDC agent tunnels Postgres to Grafana](assets/diagrams/architecture-agent-host.png#only-light)
![The agent host: five Claude Code containers reach the Claude apps gateway over HTTPS; the gateway keeps spend in Postgres, signs developers in with Cognito, calls Bedrock with its instance role and forwards telemetry, the plugin sends generations to Agent Observability and the PDC agent tunnels Postgres to Grafana](assets/diagrams/architecture-agent-host-dark.png#only-dark)

The image shows the default Claude topology; the
[architecture guide](architecture.md#on-the-agent-host) also diagrams the optional direct
Codex/pi routes.

## What runs where

| Container | Role |
|---|---|
| `gateway` | Claude apps gateway on 443 inside the compose network, hostname `touchline-gateway.internal`, TLS from a private CA Terraform generates. Published on the host at `127.0.0.1:8443` only. |
| `postgres` | the gateway's store: sessions, spend counters, caps, admin audit |
| `pdc-agent` | outbound tunnel so Grafana can query Postgres (datasource `touchline-gateway-spend`) |
| `alloy` | ships container logs and host metrics to Grafana Cloud |
| `spend-caps` | one-shot: sets the caps from `spend_caps` through the gateway admin API |
| `dev-<name>` | one per developer: the selected agent, its isolated home, shared traffic loop and local stdio MCP servers; only Claude Code runs the login bot |
| `claude-install` | one-shot: downloads the pinned Claude Code release (`claude_code_version`) and verifies its signature and checksum |

Nothing listens on the VPC. You reach the host with SSM Session Manager.

```bash
id=$(tofu -chdir=examples/complete output -raw agent_host_instance_id)
aws ssm start-session --target "$id"
cd /etc/agent-host && sudo docker compose ps
```

## Agent paths and capture

| Agent | Bedrock route | Telemetry | Important limits |
|---|---|---|---|
| Claude Code (default) | Claude apps gateway, using the instance role and team application profiles | Native Claude OpenTelemetry through the gateway; Agent Observability plugin | Gateway sign-in and spend caps; prompt deny and tool-argument redaction, no prompt redaction or tool-result guards |
| Codex | Direct Bedrock Mantle, `openai.gpt-5.6-luna` in `us-east-1` | Agent Observability CLI hooks plus native Codex OTLP with a separate token | No gateway sign-in, ledger or caps; tool names normalized to `Bash`/`apply_patch` for guards; verify real hook and native-signal coverage before presenting |
| pi | Direct team application inference profile backed by EU Haiku 4.5 | Official Grafana pi extension, completed-turn generations, token usage, tools and cost | No native Claude metrics or gateway caps; lowercase tool names; preflight PII redacts rather than denies; incomplete-turn export on termination needs verification |

Codex and pi read a uid-owned, mode-0400 AWS shared-credentials INI file at
`/run/secrets/developer_aws_credentials`. Each agent type has its own IAM user/key; personas of
the same type share that key. IMDS stays blocked. Neither gets the host ingest token. Both read
the dedicated Agent Observability client token from the rendered user config at
`/home/node/.config/agento11y/config.env`. Native Codex metrics, logs and traces use a separate
`codex_otlp_token`, mounted only in Codex services; this is not the plugin token. See
[security](security.md#non-claude-bedrock-credentials-and-rotation) for scope and rotation.

Agent Observability names are `claude-code/<prefix>`, `codex-<prefix>` and `pi-<prefix>`;
Codex/pi attach `service.namespace`, team and developer identity explicitly. Their canonical model
names are exported while pi keeps the application-profile ARN for actual routing. Pi only accepts
the priced `eu.anthropic.claude-haiku-4-5-20251001-v1:0` source profile in this first implementation;
an unpriced or different profile fails rendering. Codex similarly accepts only its priced Luna
model. Extending the model list requires checking routing, token categories and pricing together.

The JavaScript SDK is pinned to 0.13.0 and the Agent Observability CLI/Claude plugin to 0.49.0.
Those are the published stable versions checked on 15 October 2026; a deployment still needs its
installed versions and Cloud connection checked. The pi runtime and extension have separate pins
in their package lockfile. The extension's legacy `@mariozechner` peer names alias the pinned
`@earendil-works` packages, avoiding a second, obsolete pi runtime. Do not treat features on upstream
`main` as released JavaScript APIs. CLI 0.49.0 also enables
anonymous CLI usage statistics by default; `AGENTO11Y_ANONYMOUS_USAGE_STATS=disabled` opts out
independently of session content capture. This setting does not disable hooks or Cloud export.

Copilot and Cursor are deferred. The Copilot spike needs operator-provided headless authentication
for the licensed identity; permission to use a seat for a bounded spike does not authorize ongoing
traffic. Cursor needs demonstrated headless lifecycle hooks and attributable token/cost capture
before deployment. Neither licence alone enables a persona in this module.

## Sign-in (Claude Code only)

Claude Code has no non-interactive way to sign in to a gateway, so each developer container runs a
login bot at start. It drives the real Claude Code terminal UI in tmux, checks the gateway
certificate against the private CA, opens the device-verification page in headless Chromium, and
signs in on the Cognito hosted UI with the developer's generated password. Credentials persist on
a per-developer volume, so restarts keep the session.

Gateway sessions last 12 hours. Cognito issues no refresh token for this flow, so the traffic loop
signs a developer in again when a session lapses.

The bot is tested against the pinned `claude_code_version`. If you change that version and the
bot stops working, use the manual fallback and report the version.

### Manual fallback: `just login-developers`

```bash
just login-developers          # uses examples/complete by default; dir=<root> for another root
```

This opens an SSM session on the host and runs `agent-host-login-links`, which prints each
developer's verification link and waits until the sign-ins complete. The links point at
`https://touchline-gateway.internal/device?...`, and after the Cognito sign-in the browser is sent
back to `https://touchline-gateway.internal/oauth/callback` on port 443. To open them from your
laptop, run `just login-tunnel` in a second terminal. It:

1. forwards local port **443** (not 8443) to the gateway over SSM
   (`aws ssm start-session ... --parameters portNumber=8443,localPortNumber=443`); binding a port
   below 1024 may need `sudo` on Linux;
2. prints the SPKI pin of the gateway's leaf certificate (from the `gateway_cert_pem` output) and
   opens a throwaway Chrome or Chromium profile (`--user-data-dir` in a new temporary directory)
   started with `--ignore-certificate-errors-spki-list=<pin>` and
   `--host-resolver-rules="MAP touchline-gateway.internal 127.0.0.1"`. That profile accepts only
   the gateway's own key and resolves only the gateway's name to the tunnel. Nothing is added to
   `/etc/hosts` or to any system or browser trust store. If no Chrome or Chromium is found, the
   recipe prints the full command to start one yourself;
3. closes the browser and deletes the profile when you stop the tunnel with Ctrl-C.

Do not add the demo's private CA (`gateway_ca_pem`) to your system or browser trust store: the
Terraform provider cannot name-constrain it, so a trusted copy could vouch for any hostname, and
its private key sits in Terraform state. If you did trust it on an earlier version of these
instructions, remove it (macOS: Keychain Access, delete the "touchline demo private CA"
certificate; Linux: remove the file you added under `/usr/local/share/ca-certificates/` and run
`update-ca-certificates`), and remove any `touchline-gateway.internal` line from `/etc/hosts`.

Then open each link in that browser and sign in as the developer named in it. Usernames are in
`tofu output developers`, passwords in `tofu output -json developer_passwords`.

You can also sign one developer in from inside the host:
`sudo docker compose exec dev-alex-morgan dev-login --force`.

## Reaching the gateway: `just gateway-tunnel`

```bash
just gateway-tunnel            # forwards localhost:8443 to the gateway on the host
```

Then save the CA for curl (a file you pass to `--cacert`, never a trust store entry):
`tofu -chdir=examples/complete output -raw gateway_ca_pem > ca.pem`, and:

```bash
curl --cacert ca.pem --resolve touchline-gateway.internal:8443:127.0.0.1 \
  https://touchline-gateway.internal:8443/readyz

curl --cacert ca.pem --resolve touchline-gateway.internal:8443:127.0.0.1 \
  -H "x-api-key: $(tofu -chdir=examples/complete output -raw gateway_admin_read_key)" \
  https://touchline-gateway.internal:8443/v1/organizations/spend_limits/effective
```

The read key shows caps and spend. The write key stays on the host
(`/etc/agent-host/secrets/gateway/gateway_admin_write_key`).

## Developers and teams

Defaults: five Claude Code developers in three teams. The `agent` field defaults to
`"claude-code"`; set it to `"codex"` or `"pi"` on an added persona to opt in.

| Developer | Team |
|---|---|
| alex.morgan | newsroom |
| priya.shah | newsroom |
| sam.okafor | trading |
| jordan.lee | trading |
| casey.nguyen | platform |

For Claude Code, each team is a Cognito group, a gateway policy (managed settings by group) and a set of Bedrock
application inference profiles, one per model. Developer telemetry carries the team as
`user.groups`, and the gateway also stamps `team.name` in the resource attributes.

To change them, set the module inputs and apply:

```hcl
teams = ["newsroom", "trading", "platform", "data"]

developers = [
  { name = "alex.morgan", team = "newsroom" },
  { name = "robin.patel", team = "data", agent = "codex" },
  { name = "taylor.reed", team = "platform", agent = "pi" },
  # ...
]
```

- `name` is a stable key (letters, digits, dots). Email is `<name>@<developer_email_domain>`.
- Every developer's team must be in `teams` (a precondition checks this).
- **Keep `newsroom`, `trading` and `platform` in `teams`.** The in-app agents are assigned to those
  three teams and call their inference profiles.
- Only Claude Code personas get Cognito users and gateway sessions. Codex and pi start with
  file-based Bedrock credentials and never run the login bot.
- The trading team is limited to Haiku at the gateway through `team_model_allowlist` (default
  `{ trading = ["haiku"] }`). A team left out of `team_model_allowlist` gets every
  `gateway_models` entry.
- The developer list, teams, spend caps and `team_model_allowlist` live in the agent-host secret's
  `config` key, not in the host's user data. An apply that changes them updates the secret; the
  host re-reads it within 5 minutes and recreates only the containers whose settings changed, with
  no host replacement and no interruption to the Postgres spend ledger. The login bot signs in any
  Claude Code developer whose container was recreated.

## Spend caps (Claude gateway only)

Codex and pi bypass this ledger and these caps. Their local session budgets stop additional
work using reported/estimated usage. Pi may overshoot one model response; Codex may overshoot a
whole CLI turn containing multiple model/tool calls. These are not
server-enforced daily limits. See [cost](cost.md).

The gateway enforces caps in USD per period (`daily`, `weekly`, `monthly`), per organization, per
group (team) and per developer. The organization cap is a per-seat default, and the most
restrictive cap that applies wins. A developer over a cap gets HTTP 429 with the message
"touchline demo spend cap reached".

Defaults:

```hcl
spend_caps = {
  organization = { daily = 20 }                  # every developer
  groups       = { trading = { daily = 5 } }     # trading developers
  users        = { "casey.nguyen" = { daily = 2 } }
}
```

Omitting a key keeps its default; set it to `{}` to remove that level. The `spend-caps` container
applies them at every boot. Spend and caps appear on the gateway dashboard's *Spend store* tab
and the Claude Code dashboard's *Gateway spend* tab, and the gateway spend alert fires at 5% of
the organization daily cap.

Gateway spend is the gateway's own estimate from token counts, a circuit breaker rather than a
Bedrock invoice. Each unattended Claude session also has a hard whole-session budget from the prompt file
(`SESSION_MAX_BUDGET_USD`, default $1.00), shared across every turn including any follow-ups.

## Traffic

With `traffic_enabled = true`, each developer runs a scripted session every
`developer_session_interval_minutes` (20 by default, jittered) against a fresh copy of the
fictional Touchline codebase seeded into the session directory (`agent-host/codebase`): usually a
prompt written for their team, sometimes any other non-PII prompt, and a low baseline plus
occasional multi-probe bursts from one developer at a time otherwise a PII probe (`pii-*.txt`)
that the Claude/Codex preflight deny guard should block (pi instead redacts PII) -- see [the runbook's PII guard
section](demo-runbook.md#the-pii-guard-claude-code). A share of sessions continue for one to three
`--- followup` turns on the same agent conversation (Claude uses `--resume`), and some stop early
(abandoned). Prompts are in [agent-host/prompts](https://github.com/rknightion/grafana-cloud-agento11y-demo/tree/main/agent-host/prompts). Claude models are
weighted towards Haiku within the team's allowed models. Codex and pi use their single supported
model/profile. Each adapter resumes its own conversation for follow-ups; isolated home volumes
keep one agent's auth and state out of another's path. Each session writes one JSON result line
to the container log (`event=dev_session`, including `user_turns` and `abandoned`).

Run one session by hand:

```bash
sudo docker compose exec dev-priya-shah dev-session                       # random prompt
sudo docker compose exec dev-priya-shah dev-session /opt/agent-host/prompts/<scenario>.txt
```

## Observing multiple agents

Use Agent Observability's built-in **Coding agents** view as the first comparison surface: filter
to the demo namespace, then compare agent, developer, sessions, generations, tokens, tools and
estimated cost. Check that the selected time range contains completed sessions for each enabled
agent. This is an operator verification procedure, not a claim that every deployed roster already
has all three agent types. The [runbook](demo-runbook.md#comparing-claude-code-codex-and-pi) gives
the side-by-side flow and missing-data checks.

Engineering decision: retain the four existing dashboards for this rollout. Do not add a Codex or
pi dashboard until live exported signals and useful panels are established. The Claude Code
dashboard and its native `claude_code_*` alerts/recording rules remain Claude-only. Empty native
Claude panels for another agent do not indicate lost Agent Observability generations. Codex native
OTLP is an additional investigation surface; pi relies on its plugin.

## What the gateway pushes (Claude Code only)

Per team, through managed settings: Claude Code's OpenTelemetry exporters (the gateway forwards
client telemetry to the Grafana Cloud OTLP gateway with `telemetry.forward_to`), content logging
switches (from `content_capture`), resource attributes scoping everything to `service.namespace=touchline`,
the Agent Observability plugin with its tags and its agent name (`claude-code/touchline`, which the guards match on), MCP servers, and the model list. The Claude Code developer
containers carry only the three managed settings needed to find and sign in to the gateway.
