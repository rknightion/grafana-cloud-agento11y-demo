---
id: AIO-0011
title: Recreate expanded demo for next presentation
status: Done
assignee:
  - '@codex'
created_date: '2026-10-16 09:26'
updated_date: '2026-10-16 09:36'
labels: []
dependencies: []
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User requested bringing the destroyed demo back up using the saved expanded roster and aligned dashboards on the already selected stack.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Saved isolated consumer is applied successfully with synthetic traffic enabled.
- [x] #2 All eleven developer containers and application workloads are running.
- [x] #3 Fresh successful sessions arrive from Claude Code Codex and pi, with restored dashboards.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Reconcile demo state and saved immutable consumer. Inspect demo-only create plan and apply serially. Verify bootstrap, application readiness, eleven containers, fresh telemetry and restored dashboards; record actual deployment state.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Saved immutable source and all image pins reused. Fresh plan admitted181creates and6reads only under demo module; serial apply completed successfully. Kubernetes app pods all1/1Running. New host created; next bootstrap, eleven-developer and fresh telemetry validation. Evidence /tmp/touchline-recreate-20261016-apply.log; saved sensitive plan in credential tree.

Apply completed181adds0changes0destroys; all7dashboards restored with Terraform ownership. Kubernetes app pods ready. Host cloud-init completed and pinned images pulled; compose starting, no manual repair. Await fresh developer sessions before closeout.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Recreated saved immutable consumer on selected stack:181resources added0changed0destroyed, synthetic traffic enabled. All Kubernetes app pods1/1Running; all11developers running; gateway/Postgres healthy. All6Codex/pi developers completed fresh successful sessions with correct team attribution in live Loki, and fresh Claude Code successes also arrived. All7dashboards restored and Terraform-managed; dedicated/combined queries exercised against fresh data. Source/image pins unchanged, so no code tests rerun; actual saved plan/apply and runtime/API verification are operational proof. Private lifecycle documentation updated and pushed. Evidence /tmp/touchline-recreate-20261016-apply.log, /tmp/touchline-recreate-telemetry.log, /tmp/touchline-recreate-session-wait.log and /tmp/touchline-recreate-query-check.log.
<!-- SECTION:FINAL_SUMMARY:END -->
