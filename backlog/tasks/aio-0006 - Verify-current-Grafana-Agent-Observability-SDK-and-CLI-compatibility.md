---
id: AIO-0006
title: Verify current Grafana Agent Observability SDK and CLI compatibility
status: Done
assignee:
  - '@codex'
created_date: '2026-10-15 17:18'
updated_date: '2026-10-15 18:16'
labels: []
dependencies: []
type: chore
ordinal: 22000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Published stable versions are checked against demo pins using upstream release and registry evidence.
- [x] #2 Relevant released behavior changes are addressed or explicitly documented, with validation of any changed runtime behavior.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Verify released SDK/CLI versions and source contracts, retain stable pins, explicitly disable anonymous CLI statistics in the image, then verify installed versions and doctor cloud connectivity during rollout.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified upstream stable JS SDK 0.13.0 and CLI/plugin 0.49.0, retained pins. Updated image disables anonymous CLI statistics. Actual published ARM64 image prints agento11y v0.49.0; both agent doctor --require-cloud checks report generation export 202 and metrics/traces 200. Full just check passed. Unpatched SDK dependency advisory is separately tracked in AIO-0007 (braces advisory in the Google ADK dependency).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Stable SDK and CLI pins already current; compatibility review completed, anonymous usage stats disabled explicitly, current CLI verified in published image, live generation/OTLP health proven. No fabricated version bump.
<!-- SECTION:FINAL_SUMMARY:END -->
