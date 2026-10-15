---
id: AIO-0006
title: Verify current Grafana Agent Observability SDK and CLI compatibility
status: In Progress
assignee:
  - '@codex'
created_date: '2026-10-15 17:18'
updated_date: '2026-10-15 17:20'
labels: []
dependencies: []
type: chore
ordinal: 22000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Published stable versions are checked against demo pins using upstream release and registry evidence.
- [ ] #2 Relevant released behavior changes are addressed or explicitly documented, with validation of any changed runtime behavior.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Verify released SDK/CLI versions and source contracts, retain stable pins, explicitly disable anonymous CLI statistics in the image, then verify installed versions and doctor cloud connectivity during rollout.
<!-- SECTION:PLAN:END -->
