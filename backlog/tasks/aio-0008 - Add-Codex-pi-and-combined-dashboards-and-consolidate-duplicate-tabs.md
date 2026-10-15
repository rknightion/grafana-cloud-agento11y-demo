---
id: AIO-0008
title: Add Codex pi and combined dashboards and consolidate duplicate tabs
status: In Progress
assignee:
  - '@codex'
created_date: '2026-10-15 20:35'
updated_date: '2026-10-15 20:40'
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
- [ ] #1 Codex, pi and combined coding-agent dashboards are Terraform-managed in the existing demo folder and query verified telemetry.
- [ ] #2 Exact duplicated gateway tabs and repeated diagnostic panels are consolidated with useful navigation retained.
- [ ] #3 Dashboard queries are exercised against live data and rendered snapshots inspected, with any remaining gaps explicitly reported.
- [ ] #4 Dashboard-only deployment changes no host, images, traffic or credentials.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Use existing Terraform v2 template registry and Touchline folder. Add Codex/pi focused single-page runtime dashboards plus combined coding-agent comparison from real completed-session logs and verified plugin/native metrics. Consolidate 30 identical Gateway panels out of Claude and three exact duplicate diagnostics elsewhere; retain links and original source archive. Validate every new query against live data, render snapshots, apply only dashboard resources through the existing consumer with image/host inputs frozen, and inspect stored results and images.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Current implementation: seven Terraform dashboards; three new runtime/comparison views and 33 exact duplicate panels consolidated. All new query expressions exercised live: Claude Code, Codex and pi have completed records and plugin metrics. Error zeros require session evidence; native Codex TTFT suppresses division by zero and explicitly reports insufficient samples. Pending independent review, dashboard-only consumer plan/apply and rendered snapshots. Public module images must remain pinned to 0.5.0 in the consumer.
<!-- SECTION:NOTES:END -->
