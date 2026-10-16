---
id: AIO-0013
title: Vary communications workflows and separate their telemetry identity
status: In Progress
assignee:
  - '@codex'
created_date: '2026-10-16 11:44'
updated_date: '2026-10-16 11:46'
labels: []
dependencies: []
ordinal: 29000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The communications showcase gives every assistant identical call counts and inherits the base application namespace. Use real selective workflow paths and a distinct telemetry identity; update dashboard navigation to Knowledge Graph.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Actual varied workflows produce unequal assistant volumes with recorded provenance.
- [ ] #2 New communications telemetry uses its own namespace and appears separately in service discovery.
- [ ] #3 Dashboard Application Observability links point to the requested Knowledge Graph catalogue.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Vary actual showcase routes (writing-only, knowledge help, optional design review and selective retrieval) with bounded random timing. Set resource service.namespace=communications-demo and verify fresh telemetry/service identity. Update all application-observability dashboard navigation to requested Knowledge Graph URL in source and live dashboards. Query and visually verify the overlay, preserving existing demo traffic.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Dashboard lane updated all3existing Application Observability links to requested Knowledge Graph catalogue URL in public source and live Grafana; all7base dashboards verified no old navigation remains. Comms companion updated similarly. Confirmed old Knowledge Graph entity service=communications-demo-workflow has namespace=touchline; new runner/job resource attrs set namespace=communications-demo and service=communications-workflow. New runner chooses optional knowledge/design stages and writer followups with shuffled12scenario pool and timing jitter; CodeRabbit running before deployment.
<!-- SECTION:NOTES:END -->
