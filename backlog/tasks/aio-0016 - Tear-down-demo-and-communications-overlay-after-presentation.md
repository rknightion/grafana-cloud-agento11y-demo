---
id: AIO-0016
title: Tear down demo and communications overlay after presentation
status: Done
assignee:
  - '@codex'
created_date: '2026-10-16 13:13'
updated_date: '2026-10-16 13:18'
labels: []
dependencies: []
ordinal: 32000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User authorized teardown of the running isolated demo lab, including temporary communications overlay. Preserve expanded configuration for recreation and shared infrastructure.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Separate demo resources and temporary communications dashboard are removed.
- [x] #2 Demo state is empty and live absence checks pass while shared EKS remains active.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Inspect delete-only plan from separate aio11y-demo state; verify account-wide logging still belongs to demo. Remove temporary communications dashboard (source retained); namespace destruction handles overlay Jobs/ConfigMap. Apply saved serial destroy plan, verify empty state and live resource absence plus shared cluster ACTIVE; update lifecycle records.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Current saved plan admitted181delete-only resources, all under module.demo[0], no shared EKS/Grafana stack or stack-wide onboarding. Verified Bedrock invocation logging belongs to /aws/bedrock/touchline-invocations. Temporary communications dashboard deleted after readback/export. Serial saved-plan destruction running in separate root; namespace handles overlay Jobs/ConfigMap. Sensitive plan retained credential tree mode600; saved source/image pins unchanged.

Initial destruction removed180resources; remaining exact demo invocation-log bucket failed AWS provider ListObjectVersions parsing with token-too-long. Reconciled state confirms only that bucket remains. Direct AWS paginated API removed158versions/objects from that exact bucket; fresh destroy remainder plan/apply started, never replayed failed saved plan. No shared resources touched.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Destroyed181isolated demo resources plus temporary communications dashboard; namespace removal cleared overlay Jobs/ConfigMap. Initial apply failed only at invocation-log bucket provider parsing; reconciled one-resource state, paginated exact-bucket158object/version cleanup, fresh delete-only remainder apply completed. Demo state empty. Live checks prove host terminated, namespace/eightdashboards/folder/IAM users/policy/secrets/buckets/Cognito/logging absent; shared EKS ACTIVE. Current log KMS key PendingDeletion23October2026. Source/expanded roster and immutable pins retained. Operational verification used actual saved plans,apply,state and live APIs; no code tests required. Provider recurrence tracked in AIO-0017 (handle large S3 version responses during teardown). Evidence /tmp/touchline-teardown-20261016-verified.log and final-state log.
<!-- SECTION:FINAL_SUMMARY:END -->
