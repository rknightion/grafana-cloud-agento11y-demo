# Agent host seam

The contract between the Terraform that renders the agent host (`terraform/aws-agent-host.tf`)
and the files in this directory. Change a name here only together with both sides.

## Template variables (`cloud-init.yaml.tftpl`, static)

user_data never changes with a knob or a credential; changing it replaces the host.

| Variable | Type | Meaning |
|---|---|---|
| `name` | string | Demo prefix; compose project name, `service.namespace` |
| `aws_region` | string | Secrets Manager, S3 and Bedrock region |
| `secret_arn` | string | The agent-host secret below |
| `images_registry`, `images_name_prefix`, `images_tag` | string | `<registry>/<name_prefix>gateway:<tag>` and `<registry>/<name_prefix>dev-workstation:<tag>`; the tag must be plain |
| `images_digests_json` | JSON | Optional `{gateway: "sha256:...", "dev-workstation": "sha256:..."}`; a pinned image is referenced as `<ref>:<tag>@<digest>` |
| `bundle_bucket`, `bundle_json` | string, JSON | The render bundle: `{host path: {key, sha256, mode}}` in the module-owned bucket. `agent-host-install-bundle` refuses any file whose SHA-256 differs |

The bundle is every file here that runs as root: `render/render.py`, `config/alloy.alloy`,
`config/postgres-bootstrap.sh` and `host/*`. Images are pulled only when missing, never re-pulled.

## Agent-host secret (Secrets Manager, JSON, re-read every 5 minutes)

Credentials: `cognito_client_secret`, `gateway_jwt_secret`, `gateway_admin_write_key` (32+
characters), `gateway_admin_read_key` (32+ characters), `postgres_password` (gateway role),
`postgres_grafana_ro_password`, `grafana_otlp_token` (metrics, logs and traces write: gateway
`forward_to` and host Alloy only), `agento11y_client_token` (generation, metrics and traces write: the
Claude Code plugin's generations and its own OTLP export, pushed to every client), `pdc_token`, `tls_ca_pem`, `tls_cert_pem` (leaf for
`gateway_hostname`), `tls_key_pem`, `developer_passwords` (`{name: password}` for Claude Code developers only).
`developer_bedrock_credentials` is `{agent: {access_key_id, secret_access_key, region}}`,
where `agent` is `codex` or `pi`; IAM principals are scoped independently by integration.
`codex_otlp_token` is a separate metrics/logs/traces-only credential consumed solely by Codex native
telemetry, never the Agent Observability generation client token.

`config` holds every mutable knob:

| Key | Type | Meaning |
|---|---|---|
| `gateway_hostname` | string | `<prefix>-gateway.internal`; gateway URL is `https://<gateway_hostname>` (port 443) |
| `claude_code_version` | string | Claude Code release installed at container start |
| `agento11y_cli_version` | string | `latest` keeps the image's pinned build; a version installs that one. The plugin marketplace is pinned to the matching `plugins/agento11y/v<version>` tag |
| `developers` | list | `[{name, email, team, agent?, sub?}]`; `agent` defaults to `claude-code`, supported values are `claude-code`, `codex`, `pi`. Only Claude Code has a Cognito `sub` |
| `teams` | list | `["newsroom", ...]`, Cognito group names |
| `spend_caps` | object | `{organization: {period: usd}, groups: {team: {period: usd}}, users: {name: {period: usd}}}`, periods `daily`, `weekly`, `monthly`; user caps apply only to Claude Code identities |
| `gateway_models` | list | `[{key, id, source_profile, upstream_profile_arns_by_team: {team: arn}}]`, optional `upstream_profile_arn`; `source_profile` identifies the exact priced pi model |
| `codex_bedrock` | object | `{model, region}`; exact Mantle model id and request region, required for Codex developers |
| `team_model_allowlist` | map | `{team: [model key]}`; a listed team gets only those gateway models |
| `cognito_issuer`, `cognito_client_id`, `cognito_domain_url` | string | OIDC issuer, app client id, hosted UI base URL |
| `traffic_enabled` | bool | Developer sessions on or off |
| `session_interval_minutes` | number | Mean minutes between sessions per developer |
| `content_capture` | bool | Prompt, response and tool content in telemetry |
| `grafana_otlp_endpoint`, `grafana_otlp_username` | string | Grafana Cloud OTLP gateway base URL and instance id |
| `agento11y_endpoint`, `agento11y_tenant` | string | Agent Observability API URL and tenant id |
| `pdc_cluster`, `pdc_hosted_grafana_id` | string | PDC cluster slug and hosted Grafana (stack) id |
| `service_names` | map | `local.service_names`; uses `gateway` and `agent_host` |

The Cognito app client's callback URL must be `https://<gateway_hostname>/oauth/callback`.

The renderer writes each value to `/etc/agent-host/secrets/<consumer>/<key>`, mode 0400, owned by
the container uid that reads it, and removes files for secrets or developers no longer rendered.
The Postgres superuser password is generated on the host once and never leaves it. A change to
the secret re-renders within 5 minutes and recreates only the services whose inputs changed.

## Networks

| Network (bridge) | Members | Allowed |
|---|---|---|
| `<prefix>-core` (`ahcore0`, `172.30.252.0/24`) | gateway (`172.30.252.2`), postgres, one-shots, alloy, spend-caps | everything except IMDS, which only the gateway's fixed address may reach |
| `<prefix>-dev` (`ahdev0`, `172.30.253.0/24`) | developers, gateway (`172.30.253.2`) | developers: DNS, gateway:443, public internet. No IMDS, link-local, RFC 1918, CGNAT or host |
| `<prefix>-pdc` (`ahpdc0`) | pdc-agent, postgres | pdc: postgres:5432, DNS, public internet. Nothing private, no IMDS or host |

`host/agent-host-firewall` enforces the table in `DOCKER-USER` and `INPUT` (plus IPv6 drops for
`ahdev0` and `ahpdc0` in the ip6tables `FORWARD` and `INPUT` chains), before Docker starts
(a docker.service drop-in) and before every compose run; nothing starts if it fails.

## What the host provides to Grafana

- Postgres `postgres:5432` on the pdc network, database `gateway`, read-only role `grafana_ro`
  with SELECT on `spend`, `spend_limits`, `principal_emails` and `admin_audit` only (not `kv`
  or `_migrations`), reached through the PDC agent, no TLS.
- Container logs with `service_name=<prefix>-gateway` (gateway) or `<prefix>-agent-host`
  (everything else) and `service_namespace=<prefix>`; host and container metrics as
  `<prefix>-agent-host`.
- Developer telemetry through the gateway's `telemetry.forward_to`, with
  `OTEL_RESOURCE_ATTRIBUTES=service.namespace=<prefix>,team.name=<team>` and
  `AGENTO11Y_TAGS=service.namespace=<prefix>,team=<team>` pushed by the gateway policy. The
  policy also sets `AGENTO11Y_AGENT_NAME=claude-code/<prefix>`, which the Claude Code guards match
  on because the plugin's guard calls carry no tags.

## Non-Claude developer foundation

Terraform creates Cognito users, passwords and group memberships only for `claude-code` developers.
The mutable developer roster carries `agent`; omitting it retains the previous renderer behavior.
An all-Claude roster retains the compose and gateway configuration bytes checked by the synthetic
fixture in `agent-host/render/claude-baseline.json` (recorded from its `source_sha`).

Codex and pi use the existing workstation image as uid 1000, `HOME=/home/node`, and an independent
`<agent>-home-<developer slug>` volume. They receive `DEVELOPER_AGENT` and
`AGENT_STATE_DIR=/home/node/.local/state/agent-host`. They have no gateway dependency, managed Claude
settings, Claude binary/config volumes or gateway CA mounts. `NODE_EXTRA_CA_CERTS` is explicitly
empty to override the image's Claude CA default. The shared recent-prompts volume still spans the
roster, so dedupe and PII burst coordination work across agents.

The common Agent Observability environment constructor feeds both the gateway policy and each
non-Claude developer's `secrets/dev-<slug>/agento11y_config`. The latter is mode 0400, owned by uid
1000 and mounted directly at `/home/node/.config/agento11y/config.env`. It contains the dedicated
client token, never the gateway/Alloy ingest token. Its keys are the shared `AGENTO11Y_ENDPOINT`,
protocol, basic auth, tenant, client token, guard enable/timeout, auto-update and content-capture
settings, plus `AGENTO11Y_TAGS=service.namespace=<prefix>,team=<team>`,
`AGENTO11Y_USER_ID=<developer email>` and `AGENTO11Y_AUTO_CODING_AGENT_TAGS=false`. Matching OTLP and
Agent Observability tenants also receive the common OTLP endpoint/client-token settings. The
single-quoted config format rejects newline, NUL and single-quote values instead of expanding them.
Config changes participate in the service input hash; secret values stay out of compose.

Non-Claude agent names are `codex-<prefix>` and `pi-<prefix>`. This keeps a stable aggregate per agent
and demo in the Coding agents view while allowing guards to select each integration by exact name.
The slash form was rejected because its acceptance by these native integrations is unverified.
Claude retains `claude-code/<prefix>` for existing guards. Automatic repository/branch discovery
stays off; static tags and the explicit developer user identity provide deterministic attribution.

Each non-Claude developer additionally receives a uid 1000, mode 0400 INI secret mounted at
`/run/secrets/developer_aws_credentials`, containing `[default]`, `aws_access_key_id` and
`aws_secret_access_key`. `AWS_SHARED_CREDENTIALS_FILE` points there, `AWS_REGION` comes from the
integration credential and `AWS_EC2_METADATA_DISABLED=true` prevents fallback to instance metadata.
Keys stay out of compose and user data; missing credentials fail rendering. These credentials are
separate from Agent Observability's client token and from the gateway's host instance role.

Codex `SESSION_MODELS` is `<codex_bedrock.model>=1`; its credential and model regions must agree.
Pi receives `/run/pi/config.json` as another uid-owned mode 0400 secret with `provider`, `region`
and `model`. The model id is its team's application inference profile ARN, and its display name is
the canonical Claude model id. Pi `SESSION_MODELS` selects that ARN with weight 1. The first
supported model is the allowed `haiku` gateway model with source profile
`eu.anthropic.claude-haiku-4-5-20251001-v1:0`; other sources fail explicitly until their pricing is
verified. The [pi model catalogue](https://pi.dev/models/amazon-bedrock/eu-anthropic-claude-haiku-4-5-20251001-v1-0)
provides its USD-per-million-token prices: input 1.1, output 5.5, cache read 0.11, cache write 1.375.
The frozen initial limits are `contextWindow=200000` and `maxTokens=4096`.

Actual non-Claude model calls, runner lifecycle and Cloud telemetry remain deployment acceptance
checks. Keep the deployed roster Claude-only until those spikes pass; selecting an unavailable
adapter fails clearly. Never forward gateway secrets or the ingest credential to a developer.

Codex additionally mounts uid 1000, mode 0400 `/run/secrets/codex_otlp_token` and
`/run/codex/config.json`. The JSON shape is `{provider, region, model: {id, cost, contextWindow},
otel: {endpoint, username}}`, where `provider=amazon-bedrock` and `otel` selects the Grafana OTLP
endpoint/username independently from generation export. The first supported Codex model is
`openai.gpt-5.6-luna`; other models fail until their pricing is verified. Its initial USD-per-million
token rates are input 0.22, output 1.32, cache read 0.022 and cache write 0.275, with
`contextWindow=272000`, from AWS's model card short-context In-Region rates. The native token
is not present in pi/Claude mounts, common Agent Observability config or compose environment.
