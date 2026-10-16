---
id: AIO-0013
title: Vary communications workflows and separate their telemetry identity
status: Done
assignee:
  - '@codex'
created_date: '2026-10-16 11:44'
updated_date: '2026-10-16 11:49'
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
- [x] #1 Actual varied workflows produce unequal assistant volumes with recorded provenance.
- [x] #2 New communications telemetry uses its own namespace and appears separately in service discovery.
- [x] #3 Dashboard Application Observability links point to the requested Knowledge Graph catalogue.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Vary actual showcase routes (writing-only, knowledge help, optional design review and selective retrieval) with bounded random timing. Set resource service.namespace=communications-demo and verify fresh telemetry/service identity. Update all application-observability dashboard navigation to requested Knowledge Graph URL in source and live dashboards. Query and visually verify the overlay, preserving existing demo traffic.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Dashboard lane updated all3existing Application Observability links to requested Knowledge Graph catalogue URL in public source and live Grafana; all7base dashboards verified no old navigation remains. Comms companion updated similarly. Confirmed old Knowledge Graph entity service=communications-demo-workflow has namespace=touchline; new runner/job resource attrs set namespace=communications-demo and service=communications-workflow. New runner chooses optional knowledge/design stages and writer followups with shuffled12scenario pool and timing jitter; CodeRabbit running before deployment.

CodeRabbit completed modified runner review with0findings; private just check and public navigation just check passed. Published navigation-only revision65bf924 and consumer pinned to that immutable source to prevent future apply reversion. New bounded12conversation batch launched with separate resource identity, max48model calls and recorded route/stage counts; next verify unequal actual counts and new KG entity.

Verified target_info and generation metrics for service.namespace=communications-demo/service.name=communications-workflow. Knowledge Graph API now returns that Service with namespace communications-demo, alongside historical old touchline entry. Bounded varied batch has unequal live call counts and six distinct real routes including writing-only, knowledge-only, optional design and writer followup. Navigation consumer saved-plan apply completed0adds3dashboardchanges0destroys; nohost/images changed. New companion dashboard includes both historical/new namespace data and recorded route strings.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed bounded12conversation batch with26real calls:Writing11,Knowledge8,Design7;7distinctroutes,0execution failures. Writing-only conversation verified in Agent Observability. New target_info/generation metrics and Knowledge Graph API prove service.namespace=communications-demo/service.name=communications-workflow; old touchline entity remains historical. Updated all existing Application Observability dashboard navigation to requested Knowledge graph URL, preserving other content/ownership;source revision65bf924 pinned in consumer and saved Terraform apply changed only3dashboards. Companion dashboard includes historical/new telemetry and route strings; all6data queries populated, rendered snapshot inspected with visibly unequal counts. CodeRabbit0findings;public/private just check passed. Private changes committed/pushed asaf1d05b. Evidence /tmp/communications-variety-batch.log,/tmp/communications-entities-variety.json,/tmp/communications-variety-snapshot/communications-demo.png.
<!-- SECTION:FINAL_SUMMARY:END -->
