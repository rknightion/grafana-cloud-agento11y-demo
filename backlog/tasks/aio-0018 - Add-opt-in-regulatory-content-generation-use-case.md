---
id: AIO-0018
title: Add opt-in regulatory content-generation use case
status: In Progress
assignee:
  - '@codex'
created_date: '2026-10-20 21:16'
updated_date: '2026-10-21T00:35:00Z'
labels: []
dependencies: []
documentation:
  - backlog/docs/doc-0003
priority: medium
type: feature
ordinal: 34000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The demo only shows Touchline Times (sports and betting). Prospects in regulated industries ask what agent observability looks like when drafted content must be grounded, reviewed and auditable. This epic adds a second use case, regulated-document authoring (ICF and CSR drafting for a fictional sponsor), that can be enabled alone or beside Touchline through Terraform. Design and settled decisions: doc-0003 (read it first; do not re-open its decisions). Nothing from any real customer engagement may enter this public repository.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 use_cases = ["touchline"] (the default) plans with no changes against an existing Touchline deployment
- [ ] #2 use_cases = ["regulatory"] and ["touchline","regulatory"] both validate, and a live regulatory-only deployment shows traffic, dashboards, evaluators, guards and experiments with no Touchline objects
- [x] #3 Docs explain the use case, the opt-in, what telemetry holds per content_capture mode and the teardown
- [x] #4 use_cases = ["touchline"] (the default) plans 0 to add, 0 to change, 0 to destroy against the base commit, proven by the mock-provider test in doc-0003; moves only through committed moved blocks
- [ ] #5 use_cases = ["regulatory"] and ["touchline","regulatory"] plan correctly in the mock-provider tests, and a live regulatory-only deployment shows traffic, dashboards, evaluators, guards and experiments with no Touchline in-app workload objects (agent-host and shared var.name objects remain, see doc-0003)
- [x] #6 Docs explain the use case, the opt-in, what telemetry holds per content capture mode and the teardown
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Terraform use-case gating foundation is complete. The default mock-provider plan matches the exact pre-change base across 140 resource entries and 12 outputs after permanent moved mappings. Regulatory app, packaging, provisioning, observability and end-to-end validation remain outstanding; no live deployment was made.

Remaining regulatory source work landed in3b05093ff1324d1380ac83c9aef8728e20327ee6 through six parallel implementation/documentation lanes and root integration. App and Terraform provisioning are complete; source CI39506282163 passes, including private scrub. Packaging, controls, dashboards and end-to-end tasks retain exact live/publication acceptance boundaries. Regulatory image builds fail security scanning with CVE-2026-93687 in braces; signing/publish skipped. Code-scanning alert20 confirms the regulatory package path. No scanner exception was added; no live deployment or teardown occurred. SDK cost by agent is present; document/section cost allocation is still missing.

Regulatory image publication is now unblocked under the separately approved2026-10-21 exception (expires2026-11-15). Packaging task complete: both architectures and merged signature verified at immutable digest sha256:355b651a54090b1d53be31241e18364b3b3ffebe812de965be6910a83d7a428e, image run39521935151. Overall all-images workflow failed on unrelated gateway/workstation jobs; regulatory jobs succeeded. Next live acceptance still needs authorized target deployment/stack, capture-mode readback, scores, snapshots and teardown; no deployment occurred.
<!-- SECTION:NOTES:END -->
