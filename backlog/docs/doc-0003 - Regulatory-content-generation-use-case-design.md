---
id: doc-0003
title: Regulatory content-generation use case design
type: specification
created_date: '2026-10-20 21:16'
updated_date: '2026-10-20 21:24'
---
# Regulatory content-generation use case: design

Status: corrected after adversarial review (FAIL, 5 blockers); the corrections are in the sections marked "Review corrections". Parent task: see the epic that references this doc.

## Purpose

Add a second, opt-in use case beside Touchline Times: regulated-document authoring. A fictional
sponsor's medical writers use AI agents to draft sections of an Informed Consent Form (ICF) and a
Clinical Study Report (CSR, ICH E3 structure) from structured study data. The demo shows what
Agent Observability, guards, evaluators and experiments look like when output must be grounded,
reviewed and auditable. Nothing from any real customer engagement enters this repository: sponsor,
compound, studies, sites and subjects are all fictional, and document structure follows public ICH
E3 and ICF guidance only.

## Decisions taken by the maintainer (do not re-open)

- Opt-in is a Terraform `use_cases` set variable, default `["touchline"]`, so existing deployments
  plan with no change. Values: `touchline`, `regulatory`. Either, or both.
- The API-pull gateway story (the genai-otel-bridge shape) is out of scope for this repository's
  module: the maintainer covers it separately with synthkit-generated data. Do not build a mock
  vendor API or deploy the bridge here.
- Packaging: own app (`apps/regulatory`), own chart (`charts/regulatory`), own namespace, Alloy,
  service accounts and image (`gc-agento11y-regulatory`). The existing Touchline chart and agents
  image are not extended.
- The coding-agent EC2 host stays independent of `use_cases` (`agent_host_enabled`, current
  developers and teams unchanged).

## Shape (engineering choices inside that scope)

- Name prefix: new variable `regulatory_name`, default `dossier`, same validation as `name`.
  Namespace variable `regulatory_namespace`, default `dossier`. All regulatory objects derive from
  these, never from `var.name`.
- Fictional sponsor "Brindlemoor Therapeutics", compound "brindanib", studies `XQZ-301` (phase 3)
  and `XQZ-204` (phase 2). Code prefixes and name roots must not resemble any real sponsor's compound codes.
  Web-check any new sponsor, compound and code
  prefix for real-world matches before committing, and add them to the scrub test fixtures.
- Five agents from one image, mirroring Touchline's orchestrator plus specialists shape:
  `orchestrator` (plans and assembles a document request), `source` (retrieves study facts and
  tables), `drafter` (drafts a section), `reviewer` (checks a draft against the section rules and
  the source), `readability` (lay-language and reading-grade check, ICF only).
- Teams owning Bedrock application inference profiles: `medical-writing`, `regulatory-affairs`,
  `clinical-science`. These are regulatory-only and do not become Cognito groups or gateway teams.
- Document types: `icf` (purpose, procedures, risks, benefits, alternatives, confidentiality) and
  `csr` (synopsis, study design, efficacy results, safety results, discussion).
- Tools (pure functions over fictional fixtures, like apps/mcp-tools): `get_study`, `get_table`
  (a table/listing/figure with fixed numbers), `get_section_rules`, `get_prior_approved_text`,
  `readability_grade`.

## Observability story to demonstrate

- Grounding: an evaluator checks that every number in a drafted CSR section appears in the
  retrieved tables (deterministic regex plus an LLM judge for claims).
- Readability: ICF text scored against a target reading grade.
- Unsupported claim and fabricated statistic detection, scored per section.
- Patient identifier guard: subject IDs and site investigator names in tool results are redacted
  before the model sees them; a prompt-injection probe via a "source document note".
- Human review state: each request ends `approved`, `needs_revision` or `escalated`, recorded as a
  metric and log field, so review queue health and first-pass approval rate are dashboardable.
- Prompt and agent version governance: `agent_version` per approved prompt set, with an
  experiments suite comparing section-prompt variants and models.
- Content boundary: `content_capture` false shows the operational-metadata-only mode; the
  dashboard and docs say plainly what is and is not in telemetry in each mode.
- Cost and latency per document type and per section.

## Terraform and chart seams

- `locals.use_cases` is the one place `use_cases` is read. Touchline objects are gated on
  `local.touchline_enabled`, regulatory objects on `local.regulatory_enabled`. With the default,
  `tofu plan` against an existing Touchline deployment shows no changes (state addresses for
  Touchline resources must not move: use `count` gating plus `moved` blocks only where an address
  has to change, and prove no-diff).
- Bedrock profiles: `local.team_models` covers the union of teams that need profiles
  (Touchline teams when enabled, regulatory teams when enabled, plus teams of agent-host
  developers as today).
- IAM: a separate Pod Identity role and association for the regulatory agents service account,
  trusting only the regulatory cluster namespace and service account, invoking only the profiles
  of its own teams.
- Grafana: regulatory dashboards, rule groups, evaluators, guards, evaluation rules, experiments
  service account and Secrets use the `regulatory_name` prefix. Touchline's `team_checks`
  precondition applies only when `touchline` is enabled.
- The Helm release is a separate `helm_release` for `charts/regulatory`, gated by
  `deploy_workloads` and `regulatory_enabled`, with its own `chart_values_regulatory` output.

## Out of scope

- Real regulated content, real submissions, anything validated for GxP. The demo says so.
- Bridge or gateway telemetry (see decisions).
- Pharma-flavoured developers on the agent host.

## Review corrections (binding on every subtask)

### Object classification (resolves "what is a Touchline object")

Every resource and local is one of: touchline-only (gated on `local.touchline_enabled`),
always-on (agent host and shared objects, never gated by `use_cases`), or regulatory-only (gated on
`local.regulatory_enabled`). AIO-0018.01 writes this table into this doc before changing code.
Known mixed objects, none of which may be gated whole:

- The Grafana folder and the claude-code, gateway, bedrock, codex, pi and coding-agents dashboards
  (locals.tf `dashboards`) are always-on. Only the `agents` dashboard is touchline-only, and the
  alerts that link it (`al-guard`, `al-agents-cost`) must be filtered, not left to fail on an
  invalid `local.grafana_dashboard_urls["agents"]` index.
- `grafana_rule_group.recording` and `.alerts` mix Claude Code, gateway, Bedrock and Touchline
  rules. Keep the groups; filter rules inside them with a per-rule `use_case` field.
- `pii_regex`, `secrets_regex`, `content_safety`, `pii_judge`, `secret_leak_response` evaluators
  back the Claude Code, Codex and pi guards: always-on. Touchline-only evaluators are split out.
- Cognito, the gateway, `var.teams`, `team_model_allowlist` checks: agent-host side, always-on.

Epic AC#2 therefore means: a regulatory-only deployment has no Touchline in-app workload objects
(namespace, agents, site, loadgen, `touchline`-only evaluators/rules/dashboards); agent-host and
shared `var.name`-prefixed objects remain. A regulatory-only user who also sets
`agent_host_enabled = false` gets nothing Touchline-named except the shared folder.

### Terraform seams

- Do not extend `local.service_names`, `local.team_models`, `local.agent_teams`, `var.teams`,
  `var.agent_models` or the shared `bedrock_invoke` policy. They feed the agent-host secret
  (aws-agent-host.tf:181), Bedrock profile names prefixed `var.name` (aws-bedrock.tf:60) and the
  host. Add parallel `regulatory_service_names`, `regulatory_team_models`,
  `regulatory_agent_teams`, a variable `regulatory_agent_models` (role => bedrock_models key), its
  own profile resource (names prefixed `regulatory_name`) and its own invoke policy document.
  Leave the existing ones byte-identical.
- `var.images.digests` is encoded into host user data (aws-agent-host.tf:145), so a `regulatory`
  digest would replace the EC2 host. Filter `images_digests_json` to the images the host uses
  (gateway, dev-workstation). Anyone who already pinned other digests sees one host replacement:
  note it in AGENTS.md. Filter digests per chart too: charts/touchline/values.schema.json:31
  rejects unknown keys, and charts/regulatory needs its own schema.
- `team_checks`: gate only the first precondition (agent teams in `var.teams`) with
  `!local.touchline_enabled || ...`, without `count`; the `team_model_allowlist` check stays on.
- Validations: `regulatory_name != name`, neither is a `-` or `_` prefix of the other (the
  guard rules match `"${guard_prefix}_.*"`), `regulatory_namespace != namespace` (two Alloys would
  discover the same pods and double-ship logs).
- `service.namespace` carries the Helm `namespace` value. Terraform queries key on
  `service_namespace="<prefix>"` today (they agree only by default). For regulatory, the chart sets
  `service.namespace = regulatory_name` and every query and KG rule uses that same value.
- Existing resources that become conditional get `count` and a permanent `moved` block
  (`x` to `x[0]`); consumers upgrade from any older tag, so never remove them. Update the
  `terraform state rm` addresses in docs/teardown.md.
- Never duplicate `grafana_asserts_stack`, the App Observability `global` object or Bedrock
  invocation logging (account-wide). Regulatory Bedrock logs carry the Touchline-prefixed
  `lbl_service_namespace` (aws-bedrock.tf:501), so dashboards query that. Give the regulatory KG
  trace config its own priority (9001, not 9000); verify Asserts accepts it.
- `traffic_enabled` also suspends the regulatory loadgen and CronJob. Add
  `regulatory_requests_per_minute`.

### Proof of the no-diff criterion

The demo was destroyed on 2026-10-16, so there is no live state to plan against. Proof is a
mock-provider test: `terraform/tests/*.tftest.hcl` with `mock_provider` blocks (OpenTofu 1.13.1),
one `command = plan` run per `use_cases` combination, asserting which resources exist, plus a diff
of planned addresses and values between the base commit and the candidate with the `moved`
mapping applied. Wire it into `just lint` so `just check` runs it. `tofu validate` ignores
variable values and proves nothing about combinations.

### App and guard behaviour

- apps/agents records the raw tool result on the tool-execution span before the guard runs and the
  guard fails open (agent-client.mjs:38). In apps/regulatory record the guarded value, and make the
  patient-identifier guard fail closed. Docs state exactly what telemetry holds in each capture
  mode.
- `content_capture=false` leaves LLM-judge and regex evaluators nothing to score. Compute
  number-grounding and reading grade in-app as metrics so panels stay populated in metadata mode,
  and add a regulatory capture variable (`regulatory_content_capture`, default true) so the shared
  gateway setting is untouched.
- Regulatory injection probes need their own marker list ("source document note" phrasing); do not
  reuse `tool_result_markers`.
- Freeze evaluator and rule ids in this doc before .02 and .05 start. The guard-policy experiment
  suite belongs to AIO-0018.05 (the runner's `guards` target builds postflight tool-call cases, so
  preflight tool-result redaction needs an explicit runner extension).

### Release and plumbing (assigned in the subtasks)

justfile `setup`, `fmt`, `test`, `lint`, `render` and ci.yml "Install dependencies" loop over
`agents site mcp-tools` and must include the regulatory app; `.pre-commit-config.yaml` check-yaml
exclude must cover charts/regulatory/templates; examples/complete passes `use_cases` through and
outputs use `try()`; docs.toml nav, deploy/flux, deploy/argocd, Dockerfile.dockerignore, the
`images` variable description and docs/security.md list the sixth image; AGENTS.md gets the new
gotchas. There is one shared `images.tag` default, so release-please needs the new chart's
Chart.yaml, values.yaml and README (with `x-release-please-version` markers) in extra-files. The
regulatory image reuses the agents dependency tree, so it hits the braces CVE: the maintainer's
Trivy exception is scoped to the agents image only and must not be extended without a new
decision. A live check before the first release needs an image tag: build one from images.yml or
`just images-push` to a mirror.

### Open questions for the maintainer

- Baseline for the no-diff proof: this doc assumes the mock-provider proof (no redeploy of
  v0.5.0). Say so if a live baseline is wanted instead.
