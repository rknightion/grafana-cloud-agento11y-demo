---
id: AIO-0015
title: Deduplicate replayed terminal records from completed Kubernetes Jobs
status: To Do
assignee: []
created_date: '2026-10-16 11:55'
labels: []
dependencies: []
ordinal: 31000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Live dashboard checks found repeated copies of the final showcase_finished log line for completed workload Jobs, with identical source timestamps/run ids but varying observed_timestamp labels. This can inflate naive log-line counts. Communications dashboard now counts distinct run and conversation ids, while the collector replay cause remains to diagnose.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A bounded completed Job final log is ingested once or downstream replay-safe semantics are documented.
- [ ] #2 Collector checkpoint/reconnect behaviour is investigated without changing unrelated telemetry.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->
