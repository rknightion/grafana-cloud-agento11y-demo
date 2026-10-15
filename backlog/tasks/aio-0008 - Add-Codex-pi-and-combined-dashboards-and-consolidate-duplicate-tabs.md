---
id: AIO-0008
title: Add Codex pi and combined dashboards and consolidate duplicate tabs
status: Done
assignee:
  - '@codex'
created_date: '2026-10-15 20:35'
updated_date: '2026-10-15 20:47'
labels: []
dependencies: []
type: enhancement
ordinal: 24000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The deployed demo now has three coding agents but its custom dashboards remain Claude-only. Operators need dedicated runtime views and a shared comparison, without repeating gateway panels across tabs. Use verified live metrics/logs and preserve provenance differences in costs and counts.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Codex, pi and combined coding-agent dashboards are Terraform-managed in the existing demo folder and query verified telemetry.
- [x] #2 Exact duplicated gateway tabs and repeated diagnostic panels are consolidated with useful navigation retained.
- [x] #3 Dashboard queries are exercised against live data and rendered snapshots inspected, with any remaining gaps explicitly reported.
- [x] #4 Dashboard-only deployment changes no host, images, traffic or credentials.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Use existing Terraform v2 template registry and Touchline folder. Add Codex/pi focused single-page runtime dashboards plus combined coding-agent comparison from real completed-session logs and verified plugin/native metrics. Consolidate 30 identical Gateway panels out of Claude and three exact duplicate diagnostics elsewhere; retain links and original source archive. Validate every new query against live data, render snapshots, apply only dashboard resources through the existing consumer with image/host inputs frozen, and inspect stored results and images.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Current implementation: seven Terraform dashboards; three new runtime/comparison views and 33 exact duplicate panels consolidated. All new query expressions exercised live: Claude Code, Codex and pi have completed records and plugin metrics. Error zeros require session evidence; native Codex TTFT suppresses division by zero and explicitly reports insufficient samples. Pending independent review, dashboard-only consumer plan/apply and rendered snapshots. Public module images must remain pinned to 0.5.0 in the consumer.

Validation and deployment: public implementation 8f13e2c; final display fixes 5f88d644f43ef654d9153394009fcf266f611aad. Both repository just check gates passed. All seven OpenTofu templates rendered and new expressions queried live; independent review corrections applied. CodeRabbit skipped for declarative dashboard configuration and registry wiring per policy. Initial full saved plan and apply: exactly three dashboard creates plus four updates; subsequent display corrections touched only the three new dashboards. Final consumer pin retains image tag/digests 0.5.0. Grafana API confirms Terraform ownership and final query/display settings. Native Codex TTFT has insufficient observed increments; it displays an explicit gap. Earlier failed/success snapshot iterations remain distinct in local evidence.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Deployed dedicated Codex and pi dashboards plus Coding agents compared in the existing Terraform-managed folder. Consolidated 33 duplicate panels and retained time-preserving navigation across seven dashboards. Live query checks and independent rendered-image inspection passed: all three agent comparison bars, developer identities and INFO success logs are visible; Claude Overview no longer repeats Gateway tabs. Final images are under /tmp/touchline-dashboards/verified/ and Claude proof under /tmp/touchline-dashboards/claude-retry/. Codex native TTFT explicitly reports insufficient samples. Both local just check gates passed; hosted CI for final source remained pending at closeout. Existing Gateway/Bedrock category-label and raw caller-label gaps are tracked separately in AIO-0009 (improve category legends and sanitize IAM role labels). All applied changes were dashboards only.
<!-- SECTION:FINAL_SUMMARY:END -->
