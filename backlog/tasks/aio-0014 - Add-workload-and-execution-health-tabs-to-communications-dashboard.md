---
id: AIO-0014
title: Add workload and execution health tabs to communications dashboard
status: Done
assignee:
  - '@codex'
created_date: '2026-10-16 11:52'
updated_date: '2026-10-16 11:56'
labels: []
dependencies: []
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add useful workload and operational context around the communications assistants while retaining direct navigation to Agent Observability for conversation internals.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Workload tab shows real scenario route language and activity distributions.
- [x] #2 Execution health tab shows supported operational metrics without fabricated results or empty panels.
- [x] #3 Dashboard queries and all tabs are verified live and source is saved.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Add Overview/Request mix/Execution health tabs using verified existing metric histograms and workflow logs. Deduplicate run/conversation ids to handle terminal-log replay. Use normal operational dashboard language per user correction, preserving provenance in raw records and runbook. Query all panels, render each tab and save private source.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
User correction incorporated: normal operational wording and no synthetic/real-Bedrock presentation commentary in dashboard; provenance retained in source/raw records. Built Request mix6panels and Execution health6panels around original Overview. Verified4products/3languages/9channel-formats/7routes and P95histograms. Terminal-log replay discovered; batch counter now counts distinct run_id (3), workflow mix uses distinct conversation_id. All18data queries return populated results, including actual0execution failures and1output-cap hit.

One temporary workflow aggregation expression failed parsing during verification; corrected before final deployment and all18data queries now pass with results. Request mix and Execution health screenshots show populated panels; output-limit count1 is amber and true execution failure0 stays green. Removed provenance/implementation commentary from visible titles and intro per user correction; raw records remain unchanged. Duplicate terminal-log ingestion recorded separately; run/workflow counts use distinct ids.

Final render confirms Overview normal wording and populated corrected workflow query; Request mix and Execution health show all intended data.19panels referenced exactly once with unique ids. Added replay-safe distinct counts. CodeRabbit skipped for declarative dashboard JSON per policy; actual query and render validation are proof. Private just check running as repository gate.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added3tabs with19panels: original Overview plus Request mix(activity,routes,stages,products,languages,channels) and Execution health(completed workflows,actual failures,output caps,unique processing runs,P95duration,stop reasons). All18data queries return real results;3tabs rendered/inspected and independent review found no material issues. Fixed temporary query syntax issue before final proof; unique-id aggregation prevents replayed terminal logs inflating workflow/run counts. User presentation correction applied: normal operational wording, no synthetic/real-Bedrock commentary in visible dashboard; raw records/provenance unchanged. Private just check passed;CodeRabbit skipped declarative dashboard config. Saved private source commita385e97. Collector replay cause tracked in AIO-0015 (deduplicate replayed terminal records from completed Jobs).
<!-- SECTION:FINAL_SUMMARY:END -->
