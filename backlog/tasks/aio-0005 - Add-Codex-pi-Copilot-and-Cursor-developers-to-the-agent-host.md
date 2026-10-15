---
id: AIO-0005
title: 'Add Codex, pi, Copilot and Cursor developers to the agent host'
status: In Progress
assignee:
  - '@codex'
created_date: '2026-10-14 11:57'
updated_date: '2026-10-15 17:50'
labels: []
dependencies: []
references:
  - >-
    https://grafana.com/docs/grafana-cloud/observe-and-act/agent-observability/guides/instrument-coding-agents/
  - 'https://github.com/grafana/agento11y/tree/main/plugins'
documentation:
  - backlog/docs/doc-0002 - Research-Codex-pi-Copilot-and-Cursor-developers.md
priority: medium
type: feature
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The agent host only runs Claude Code developers, so the demo shows Agent Observability for one coding agent. Grafana ships agento11y integrations for Codex, Copilot CLI, pi and Cursor, and the app has a built-in Coding agents view that compares agents side by side. This parent groups the work to run those agents next to Claude Code.

Research, canonical sources and per-agent facts: doc-0002 (read it first). Canonical sources are the Grafana guide https://grafana.com/docs/grafana-cloud/observe-and-act/agent-observability/guides/instrument-coding-agents/ and plugins/<agent>/README.md in grafana/agento11y at the pinned tag.

Decisions already taken by the maintainer (do not re-open):
- Scope: Codex and pi are implemented. Copilot and Cursor each start with a go/no-go spike that the maintainer signs off before any implementation.
- Model access: a scoped Bedrock credential (new IAM principal) in the agent-host secret. No loop budgets, no AWS Budgets alarm, no data-residency constraint (a US region for OpenAI-on-Bedrock is fine). The Claude apps gateway is not used by the new agents. Developer containers still never reach IMDS.
- Hosting: the same agent host. All render.py, bundle and seam changes ship in one release with one planned host replacement.

Ordering and ownership: AIO-0005.01 owns render.py, SEAM.md, variables.tf and the shared session scripts. AIO-0005.05 owns terraform/grafana-agento11y.tf. The agent tasks add their parts through those seams. Copilot or Cursor work that lands after the rollout causes a second host replacement; batch it if both go ahead.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Codex and pi developers run unattended next to the Claude Code developers, and their sessions appear in the Agent Observability Coding agents view with agent, user, team, model and tokens
- [ ] #2 Guards deny the same classes of destructive and secret-reading tool calls for Codex and pi as for Claude Code, and docs state each agent's guard gaps
- [ ] #3 Copilot and Cursor each have a recorded go/no-go decision signed off by the maintainer, and are implemented or closed accordingly
- [ ] #4 The rollout replaced the host once, and Claude Code traffic, dashboards and guards behave as before
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
2026-10-15: verify current SDK releases and compatibility; implement the shared foundation, then scoped credentials and evidence-led Codex/pi spikes; integrate only agents whose live checks pass; review and gate the final candidate; publish images before one coordinated demo-root rollout. Copilot/Cursor remain go/no-go decisions after refreshed feasibility evidence. Preserve unrelated private consumer working state.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Session state revision 1 (2026-10-15): user approved full demo deployment and latest module, existing demo stack confirmed; Copilot existing seat bounded spike only; Cursor deferred. Root owns tracker, Dockerfile, justfile, credentials/live operations, consumer and landing. foundation_render owns Terraform/render/seam; foundation_runtime owns session shell/library/Claude adapter/tests. Read-only codex_spike_prep/pi_spike_prep active. SDK JS 0.13.0/CLI 0.49.0 already latest stable. private consumer shared checkout has existing unmerged root lockfile; isolated detached consumer worktree [private consumer worktree] initialized. Separate demo state has no resources/outputs, so fresh deployment. No apply/credential creation yet. Next: finish foundation, validate Bedrock endpoint/model, run bounded agent spikes, integrate passing agents, review/gate/publish then deploy.

Correction to session state revision 1: Copilot spike now deferred by maintainer pending authentication setup. Cursor remains deferred. Codex model card confirms /openai/v1/responses is correct even though model discovery uses /v1/models; nonstream request timed out, one bounded streaming probe pending. Do not override inference endpoint based on catalog path.

Session state revision 2: foundation runtime and renderer local tests pass (9 and 4 respectively). Bedrock credential lane returned validated candidate. Renderer now owns credential/config integration; pi_adapter owns pi adapter/package/tests; agent_guards owns guards/suites and experiment runner/tests. Root owns Dockerfile/justfile/CI, native Codex token wiring and deployment. Live us-east-1 Mantle streaming inference with openai.gpt-5.6-luna succeeded at /openai/v1/responses. Copilot and Cursor both deferred. No cloud mutation yet. Isolated consumer main_override.tf points to local module for preview only; do not commit override or apply local mutable source. Final deployment requires published images and immutable source.

Public preflight: removed private deployment references from this session tracker notes before review. Existing private scrub prefix regex falsely matched an upstream ip-address semver in the new lockfile; constrained it to a complete four-octet IPv4 shape, verified actual address/CIDR still fail and the semver does not, and synchronized the private CI denylist. No scanner exclusion or dependency change.

Session state revision 3: all code lanes returned; complete-package Codex arm64 Docker stage checksum and Sigstore verification passed. Full just check passed before final timeout correction; corrected runtime suite now 16 passing tests. Scoped credential/renderer/guards/pi/Codex integration and docs staged (51 files); private scrub passes. Codex nested sandbox failed under intended Docker restrictions, so adapter now uses task-approved container boundary while retaining managed hook trust. Security reviewer active. Full developer image build failed only fetching existing pinned base metadata (local registry transport timeout); host registry GETs work, bounded explicit pull pending. No deploy yet; preview succeeded with 165 creates and no changes/deletes. Copilot/Cursor deferred by maintainer. Next: security fixes, CodeRabbit, final gate, immutable image publication, paused-traffic apply and bounded live proof.

Independent security review found one major producer/consumer mismatch: native Codex token existed as a Grafana resource but was omitted from host secret. Fixed by passing codex_otlp_token with an all-Claude-safe empty fallback; tofu validation passes. Live rendered-secret check remains part of rollout. CodeRabbit final candidate review running; no landing or apply yet.

CodeRabbit completed full candidate review with four minor issues and no major/critical findings. Fixed duplicated prose, native Codex service.namespace tagging, guard suite model attribution, and false-positive secret path patterns; targeted tests/validation pass, namespace regression was observed red then green. Delta review running on code corrections. Pi legacy peer aliases are pinned to current runtime and npm audit reports zero vulnerabilities. Maintainer approved API-only live verification this session, with visual Coding agents criterion left pending.

CodeRabbit full review completed with four minor issues, all corrected; delta review completed with zero findings. Final reviewed just check in progress. Consumer work must use a fresh origin/main checkout: the older shared checkout is diverged and has an unrelated merge conflict. Preserve it; only demo-root consumer paths are authorized.
<!-- SECTION:NOTES:END -->
