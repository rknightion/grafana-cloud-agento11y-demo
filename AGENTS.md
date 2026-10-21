# grafana-cloud-agento11y-demo

The public Touchline AI observability demo: a Terraform module (`terraform/`), the `touchline` Helm
chart (`charts/touchline/`), the app images (`apps/`) and the EC2 agent host (`agent-host/`). It is
a public repository, so nothing committed here may name a customer, an account id or a credential.
`tools/scrub_check.py` and the private `.scrub-denylist` in pre-commit are the gate.

## Task tracker

Backlog.md in `backlog/`, prefix `AIO`. `backlog task list --plain --exclude-status Done` is the
queue.

- Statuses are `To Do`, `In Progress`, `Parked`, `Done`. `Parked` means attempted and blocked,
  with a concrete resume boundary.
- This public board deliberately does not carry the loop protocol (doc-0001 says why). Never
  import a copy here.

## Task interface

`just check` is the gate (fmt-check, `tofu validate`, tflint, helm lint and kubeconform, shellcheck,
scrub, Node tests), including offline use-case plans and the default compatibility fixture.
The mock-provider checks use OpenTofu 1.13.1 or newer. `just ci` adds image builds and needs Docker. `tofu -chdir=terraform validate`
needs `tofu -chdir=terraform init -backend=false` after a provider lock bump.

## Releases

release-please cuts `vX.Y.Z` from conventional commits. Its PR bumps `terraform/variables.tf`
(the `images.tag` default), the chart version and appVersion, and the reference docs. The images
workflow publishes `ghcr.io/rknightion/gc-agento11y-<app>:<version>` on release. A consumer
can pin `?ref=vX.Y.Z` only after those images exist. Releases up to v0.2.0 predate the rename: their
images carry the former repository name as prefix (see CHANGELOG.md) and must stay pullable.

## Gotchas

- **Changing the image tag replaces the agent host.** `images.tag` is rendered into the host's
  user data, so a module bump that moves the tag destroys the EC2 host. The gateway Postgres lives
  on it with no separate volume, so spend history resets and developers sign in again (about 30
  minutes before the Claude Code and gateway dashboards fill).
- **`traffic_enabled` does not replace the host.** It lives in the agent-host secret, which the host
  re-reads within 5 minutes, and in the chart values, which scale the load generator to 0 and
  suspend the `site-browser` and `experiments` CronJobs.
- **A new counter series can arrive already holding its first increments**, so `increase()` reads
  0. In an `increase(...) or (X unless X offset 30m)` alert, keep the left side `> 0`, or its
  zero-valued series hides the new-series branch.
- `agento11y_hook_evaluations_total` files pass traffic under `rule_id="none"`. Per-rule guard
  outcomes, including passes, are on `agento11y_hook_rule_outcomes_total`.
- The experiments CronJob fires on 70% of its hourly slots and picks one suite from
  `apps/agents/config/suites/` by weight (`apps/agents/experiments/run-experiment.mjs`), so a
  completed job with `"fires": false` is expected.
- The Claude Code plugin ignores guard transforms on prompts and never sends tool results, so
  Claude Code redaction only works postflight on tool arguments. Guard `priority` is the tier
  order documented in `docs/security.md`; keep deny rules below 10.
- The Experiments overview reads `last_over_time(agento11y_experiment_*)` over the picker range.
  After downtime a short range shows nothing; widen it before assuming data is missing.
- `developers[].agent` defaults to `claude-code`; Codex/pi are opt-in and use isolated homes,
  scoped per-agent-type IAM keys via 0400 shared-credentials files, no IMDS and no gateway caps.
  Codex is priced only for `openai.gpt-5.6-luna` in `us-east-1`; pi requires the priced EU Haiku
  4.5 source profile. Local budgets can overshoot an in-flight call.
- Non-Claude plugin names are `codex-<prefix>` and `pi-<prefix>`. Pi reads the rendered user
  Agent Observability config file and captures completed turns; interrupted-turn export needs
  verification. Codex native OTLP has its own metrics/logs/traces token, separate from plugin auth.
- Codex guards use canonical `Bash`/`apply_patch`; pi uses lowercase `bash`/`read`/`edit`/`write`.
  Pi preflight PII redacts rather than denies. New Codex/pi regression suites stay manual-only
  until the scheduler accounts for the enabled roster.
- The combined Coding agents dashboard compares completed-session logs across Claude Code, Codex
  and pi. Dedicated Codex/pi dashboards use their verified plugin/native signals; native
  `claude_code_*` dashboards/alerts/rules remain Claude-only. Gateway audit and spend tabs live
  only in the Gateway dashboard. Reported session costs are estimates, not the gateway ledger.
  Copilot and Cursor are deferred pending their recorded resume conditions.
- The App Observability `team` span-metrics dimension has no API or Terraform resource. Adding it
  is a manual step in the stack's Application Observability settings.
- Codex 0.162.1 suppresses custom OTLP metrics when `analytics.enabled=false`; enable it only with
  explicitly configured operator exporters. Its agento11y hook reports provider `codex` and no cost.
- Pi 1.2.0 needs explicit `-e builtin:mcp` when using `--no-extensions`. Its prompt transform
  redacts model context, not the original full-content telemetry; a mid-turn SIGTERM can lose the
  unfinished generation.
- Parallel creation of Agent Observability rules returned partial HTTP 500s during live rollout.
  Read back actual rules before retrying, then apply missing rules with `-parallelism=1`; never
  assume a failed batch created nothing. Permission-check timeouts can also surface as HTTP 403.
- The agents image has a maintainer-approved exception for CVE-2026-93687 in its installed
  `braces` package, expiring 2026-11-15. Its YAML is scoped only to that image and package path;
  remove it when an upstream fix is adopted, and never extend it without a new decision.
- New non-Claude home volumes need the `.local` parent and state directories owned by uid1000.
  Creating only `.local/bin` leaves its parent root-owned and causes a restart loop. The v0.5.0
  rollout corrected the two fresh volume parents in place; the image now creates them explicitly.

<!-- BACKLOG.MD GUIDELINES START -->
<!-- backlog.md-instructions-version: 1.53.0 -->
<CRITICAL_INSTRUCTION>

## Backlog.md Workflow

This project uses Backlog.md for task and project management.

**At the beginning of each conversation in this project, run `backlog instructions overview` before answering or taking action. Re-read it only if you have not read it yet in the current conversation.**

Use the overview to decide whether to search, read, create, or update Backlog tasks.

Before task lifecycle actions, read the matching detailed guide:
- `backlog instructions task-creation` before creating or splitting tasks
- `backlog instructions task-execution` before planning, changing status or assignee, adding a plan or implementation notes, or implementing task work
- `backlog instructions task-finalization` before checking acceptance criteria, writing final summaries, or moving tasks to terminal statuses

Use `backlog <command> --help` before running unfamiliar commands. Help shows options, fields, and examples.

Do not edit Backlog task, draft, document, decision, or milestone markdown files directly. Use the `backlog` CLI so metadata, relationships, and history stay consistent.

</CRITICAL_INSTRUCTION>
<!-- BACKLOG.MD GUIDELINES END -->

- Loki instant metric results need all-values bar-gauge rendering for multi-agent comparisons;
  retain label-based display names. Session-log panels set both `level` and `detected_level`
  from `is_error`, because ingestion can misclassify the literal `is_error=false` as an error.

- Pi uses a managed IAM policy for its explicit team/profile union: three teams exceed IAM
  users’ 2,048-character inline-policy limit. Keep the 6,144-character managed-policy check and
  exact profile/model restrictions; never widen ARN patterns to work around policy size.

- `use_cases` gates the in-app workload only; the gateway, coding-agent host, shared Grafana
  folder and coding-agent protection remain independent. Regulatory has its own app, chart,
  namespace, profiles, role, guards, evaluators and dashboard.
- Permanent `terraform/moved.tf` mappings preserve upgrades from pre-use-case resource addresses.
  Never remove them. `chart_values` and `agents_role_arn` are null without Touchline.
- Host user data now includes only gateway and dev-workstation digest pins. Existing deployments
  that pinned other images have one host replacement on upgrade; later regulatory digest changes
  cannot replace the host. That one replacement still resets the gateway ledger and sign-ins.

- Regulatory `namespace` chart value is the telemetry prefix (`regulatory_name`); Helm's release
  namespace is `regulatory_namespace`. Keep them distinct so custom namespaces retain correct
  queries. `regulatory_content_capture` does not change the shared gateway content setting.
- Regulatory review states are simulated, never human approval. Guard transport failures and
  unsafe/untransformed subject identifiers fail closed before model input and content recording.
  Metadata mode still emits in-app grounding and reading-grade metrics.
- Regulatory source-note injection markers, preflight experiment cases and guard IDs are separate
  from Touchline. New rules need serial apply and readback; local stub proof is not live scoring.
- The regulatory image has a separately maintainer-approved CVE-2026-93687 exception dated
  2026-10-21, scoped only to its installed braces package path and expiring 2026-11-15. Keep it
  separate from the agents exception, remove it when fixed, and never renew without a new decision.

- Regulatory source-note remote detection starts as warn at priority 10 with short_circuit=false;
  the app still rejects known markers before model input. Guard-policy experiments require a
  failed evaluation for the exact rule. Promotion to deny needs reviewed warning outcomes and
  the detector moved into the below-10 deny tier.
- The regulatory Deployment load generator runs continuously until shutdown. MAX_REQUESTS is
  an explicit test/manual bound only; zero requests per minute sends nothing and scales it to 0.
- `apps/regulatory/.npmrc` matches agents' legacy-peer-deps setting to exclude the SDK's unused
  optional Strands integration. Keep lockfile generation, clean installs and Docker resolution
  aligned; automatic peer installation adds hundreds of unused packages and extra audit findings.

- Regulatory cost estimates use bounded document/section/role/model dimensions and only verified
  uncached EU Haiku4.5/Sonnet4.6 rates in eu-west-1. Unknown pricing emits an unpriced-generation
  count, never a fake zero cost; stub tokens and orchestrator aggregates are excluded.
- The pinned experiment SDK stringifies recordIO input; serialize structured request/source
  evidence to JSON explicitly or judges receive only the literal [object Object].
- A new cost counter series must take its raw-value unless-offset branch before increase, so
  later increments do not hide the first returned generation's cost. Preserve observed zeros.
