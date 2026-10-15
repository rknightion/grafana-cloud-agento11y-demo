---
id: AIO-0005
title: 'Add Codex, pi, Copilot and Cursor developers to the agent host'
status: Parked
assignee:
  - '@codex'
created_date: '2026-10-14 11:57'
updated_date: '2026-10-15 20:13'
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

Session state revision 4: implementation landed ed451c229035c30794e42db647116ffff328e09e; scan-evidence wiring landed 1ee77c5cc813d4d49dc09e05b1fabc150ade48ea. CI failed the TERM-resistant child check on Ubuntu; fix uses dedicated Python process group supervisor and unchanged tests pass macOS/Linux. Repair review running. Gateway image scan reproduced seven fixed Perl advisories; apt upgrade rebuild now has zero fixed high/critical findings. Agents image has only unpatched braces CVE-2026-93687 via unused Google ADK; owner decision pending for dated exception vs hold/remove. Dev-workstation both architectures built/scanned/signed successfully for ed451c2; all images must still publish exact final version before apply. No cloud infrastructure mutation. Full mixed preview 176 creates/0 changes/0 deletes. Current consumer deploy worktree is separate latest origin/main checkout; old dirty main preserved.

Session state revision 5: scoped prerequisites and new guard rules applied (27 resources total), no agent host/workloads yet. Codex/pi real ARM64 initial/resume + MCP + generation/user/model/token proof succeeded; pi priced cost present, Codex plugin provider/cost limitation documented. Corrected explicit builtin:mcp for pi and analytics custom-metrics gating for Codex; native metrics now observed. Real destructive and secret reads denied, fake tool key redacted before file write for both. Pi SIGTERM after first stream update yields no generation (documented). Gateway patch clears local scan; agents image blocked solely by no-fix braces advisory, owner disposition still pending. Process supervisor repair review final delta active. Next: land reviewed repairs, publish successful images, complete reviewed full apply only after advisory decision; visual proof explicitly deferred by owner.

Session state revision 6: source repairs landed e5672d7, docs 83f8c0d; local gate/CodeRabbit clean. GitHub check+scrub passed for 83f8c0d, aggregation finishing. Five completed tasks: foundation, scoped credentials, guards, docs and SDK compatibility. Codex/pi implementation and API spikes pass; browser criteria explicitly deferred. Full rollout blocked by owner advisory disposition, with 27 prerequisite resources already applied and no host/workloads. Gateway/dev-workstation exact e5672d7 images published; agents image still older because CVE-2026-93687 gate is enforced. Prepared private consumer worktree remains uncommitted and must receive final immutable release/images before full serial apply. Never apply the all-Claude compatibility plans. Copilot/Cursor deferred by maintainer.

Final CI evidence: run 38784447965 completed success at exact source/docs SHA 83f8c0db514b526f7ab97ad43b84de17beef45fc. Images run 38784029713 at e5672d7 completed failure solely for the agents advisory; five other image families published. No scanner exception applied. Current-code local tests and all previously recorded live proofs remain valid; subsequent closeout changes are tracker/documentation only.

Resume revision 7: maintainer approved advisory exception then deploy. Existing destination and API-only visual deferral remain binding.

Resume revision 8: v0.5.0 created at 6f5af7b08ba9b4c7d5215f30fa48370b882ef0af, approved exception commit bca1069 included. Release image run 38797356153 and release CI 38797355101 pending/running. Existing live state rechecked: 27 prerequisites, no instance/Helm release. Private consumer checkout fast-forwarded to current origin before changes; no duplicate provisioning.

Resume revision 9: immutable v0.5.0 images for both architectures and all six cosign identities verified. Private consumer now pins release plus digests and defaults enabled=true. Saved full plan149 creates/no changes/no deletes is actively applying serially with traffic=false; original apply session retained, do not restart. State before apply contained27 prerequisites. Consumer full gate running after local cache initialization; shared root is never applied.

Resume revision10: v0.5.0 fully deployed and enabled, final serial drift plan exits0/no changes. One fresh EC2 host, all seven developer containers running, all in-cluster services ready, loadgen1/CronJobs active. Real deployed Claude/Codex/pi generation readback and native metrics confirmed; gateway ledger populated. Startup root-owned .local issue fixed on only the two new volumes; durable Docker fix and macOS-only supervisor race correction under review. Remaining acceptance is previously deferred browser proof; Copilot/Cursor remain deferred. Advisory exception expires2026-11-15 and upstream task stays parked.

Deployment goal complete via API verification. Remaining board parks: explicitly deferred visual checks, Copilot/Cursor choices, and upstream braces patch tracking. Exception is approved/deployed; it no longer blocks rollout. Final local follow-up fixes are being reviewed/landed; no running cloud mutator remains.

Closeout revision11: deployed v0.5.0 and active traffic verified; exact release and private consumer CIs green, no drift. Follow-up Docker home-parent and Darwin exit-race fixes pass full local gate, Linux runtime suite and three repeated macOS suites; both CodeRabbit reviews complete with zero findings. Landing these for future builds; running immutable v0.5.0 keeps its corrected persistent home volumes.
<!-- SECTION:NOTES:END -->
