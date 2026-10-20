---
id: AIO-0018
title: Add opt-in regulatory content-generation use case
status: To Do
assignee: []
created_date: '2026-10-20 21:16'
updated_date: '2026-10-20 21:24'
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
- [ ] #1 use_cases = ["touchline"] (the default) plans with no changes against an existing Touchline deployment
- [ ] #2 use_cases = ["regulatory"] and ["touchline","regulatory"] both validate, and a live regulatory-only deployment shows traffic, dashboards, evaluators, guards and experiments with no Touchline objects
- [ ] #3 Docs explain the use case, the opt-in, what telemetry holds per content_capture mode and the teardown
- [ ] #4 use_cases = ["touchline"] (the default) plans 0 to add, 0 to change, 0 to destroy against the base commit, proven by the mock-provider test in doc-0003; moves only through committed moved blocks
- [ ] #5 use_cases = ["regulatory"] and ["touchline","regulatory"] plan correctly in the mock-provider tests, and a live regulatory-only deployment shows traffic, dashboards, evaluators, guards and experiments with no Touchline in-app workload objects (agent-host and shared var.name objects remain, see doc-0003)
- [ ] #6 Docs explain the use case, the opt-in, what telemetry holds per content capture mode and the teardown
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->
