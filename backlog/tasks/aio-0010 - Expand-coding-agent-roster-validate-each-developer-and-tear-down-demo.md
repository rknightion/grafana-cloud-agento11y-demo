---
id: AIO-0010
title: Expand coding-agent roster validate each developer and tear down demo
status: Done
assignee:
  - '@codex'
created_date: '2026-10-15 22:01'
updated_date: '2026-10-15 22:18'
labels: []
dependencies: []
ordinal: 26000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User requested three developers each for Codex and pi, one per team, followed by destruction of the demo lab after live validation. Preserve reproducible expanded configuration and fix fresh-home startup for the next demo.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Consumer defines five Claude Code, three Codex and three pi developers across all teams.
- [x] #2 Each non-Claude developer completes a live session and appears in telemetry and dashboard grouping.
- [x] #3 Saved configuration uses a workstation image with the fresh-home permissions fix.
- [x] #4 Demo-only resources are destroyed after validation with shared cluster and unrelated workloads preserved.
- [x] #5 Pi and Codex dashboards align with Claude Code styling and supported data; no unsupported empty panels remain.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Inspect immutable edge workstation image provenance for the fresh-home fix; pin only that image alongside the expanded 5/3/3 roster. Review the saved demo-root plan and apply. Verify six non-Claude developers complete sessions, their team attribution and dashboard grouping. Then plan and apply destruction of only the separate demo root, reconcile state and live resources, and preserve the enabled configuration for deliberate recreation.

User additionally requested child-agent dashboard parity before teardown. Child implemented three tabs per runtime (Overview, Cost and tokens, Tools and guards), using only query-proven data and removing unsupported native TTFT. Integrate with IAM fix, deploy, inspect all tabs and validate expanded roster before destruction.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified immutable workstation image digest against registry manifests for amd64/arm64: build revision 0608be34b07d64104b8b995b5f763ae80b80145c, successful images CI 38800185718. Pinning it changes static user data and replaces the disposable host; user informed. Expanded roster preserves existing platform identities and adds one developer for each runtime in newsroom/trading. Consumer just check passed. Teardown is restricted to the separate demo state, never the shared cluster root.

Independent review found no blocker. Saved expansion plan changes only pi team-profile policy, demo host replacement, demo secret version and demo Helm values. Registry and successful image CI prove the pinned fresh-home fix. Destroy admission will reject any non-demo resource address or global App Observability/Knowledge Graph singleton and verify Bedrock logging ownership first.

Live expansion exposed IAM inline-user policy aggregate limit: three-team pi policy exceeds 2048 characters. Apply removed old host then failed at PutUserPolicy; no replacement host exists yet. Fix keeps the exact generated permissions but stores pi policy as a managed policy with a 6144-character precondition; Codex remains inline. Re-plan required after this partial apply; never replay the saved plan.

AWS official documentation confirms user inline aggregate limit 2048 and managed policy limit 6144 (https://repost.aws/knowledge-center/iam-increase-policy-size). Full public just check passed after policy change. Independent review confirms unchanged permissions and correct attachment/key destroy ordering. Separate demo state contains only module.demo[0] addresses, with no stack-wide appo11y/Knowledge Graph singleton. Live Bedrock logging points to /aws/bedrock/touchline-invocations.

Dashboard child completed Codex22/pi21 panels in three tabs aligned with Claude style. All41 data queries returned real six-hour series. Removed unsupported native TTFT instead of retaining an empty panel. Full combined source just check passed; templatefile render passed for both revised dashboards. Visual proof waits for deployment.

CodeRabbit completed IAM review: one major migration-order finding fixed by attaching managed policy before reducing existing inline policy to the exact profile-only subset. Corrective delta review completed with one minor size-guard finding, also fixed. Measured real three-team policy:2269chars full and661chars retained subset. Both policy sizes are guarded; permissions unchanged. No new tests added for declarative IaC; validate, tflint, full just check and live plan/apply are the proof.

Current resume boundary: public source248f699772ccfb39baad8f8ecfd18cd3b2530270 pushed; private consumer938ca42 pushed,5/3/3 roster, corrected workstation digest6559f047..., source pinned248f699. Fixed plan process running against isolated demo root; prior old host absent after partial apply. Next inspect fixed plan, apply, prove11containers and all6non-Claude successful sessions, render all6dashboard tabs, then destroy separate root. User requested child parity work before teardown; child candidate integrated. No teardown has started.

Fixed apply completed4adds3changes0destroys, including replacement host creation and both parity dashboards. New host is SSM-online with cloud-init still running. Six dashboard tab PNGs rendered to /tmp/touchline-parity-snapshots/. No teardown yet; next verify startup and fresh6persona telemetry, then inspect snapshots and destroy.

Visual inspection passed the Overview, Cost and tokens and Tools and guards tabs for both runtimes: real values, named developer/team bars, tool and guard breakdowns, no No data panels. Correct tab URLs use dtab slugs; the first numeric-tab render attempt only showed Overview and is not counted. Correct six-tab evidence is /tmp/touchline-parity-correct-tabs/. Fresh host has six non-Claude services with writable homes/credential access; first new-team completed sessions are arriving. Live IAM readback confirms attached full policy and exact inline subset.

Fresh-host validation succeeded:11developer containers running, healthy gateway/Postgres, all6non-Claude homes writable without manual repair, and all6produced is_error=false completed sessions with correct developer/team labels in Loki. Evidence /tmp/touchline-roster-host-validated.log and /tmp/touchline-roster-telemetry-final.log; bounded SSM watcher reached running=11 completed_nonclaude=6. All53queries across dedicated+combined dashboards now return data. Final expanded screenshots being captured while destroy plan refresh runs; no destroy apply yet.

Validation complete: all6fresh non-Claude sessions succeeded, all11containers running, all53queries return real series; expanded Overview snapshots visibly show3developers and all3teams for both runtimes. Saved destroy plan admitted181delete-only demo resources; no shared EKS, Grafana stack or stack-wide onboarding. Authorized teardown apply now running via isolated consumer; pending final state and live absence checks. KMS seven-day pending deletion is expected.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented and validated5Claude Code/3Codex/3pi developers, with one non-Claude developer per team. Corrected fresh-home image is digest-pinned. Fixed the actual three-team IAM policy-size failure without broadening permissions; CodeRabbit migration-order and size-guard findings corrected. Child agent aligned Codex/pi dashboards with Claude-style Overview, Cost and tokens, Tools and guards;22/21panels, unsupported TTFT removed. All11containers ran; all6non-Claude personas completed fresh successful sessions; all53dashboard queries returned data and six tab snapshots were inspected, including3developer/team breakdowns. Local gates passed and exact source CI38815202496 succeeded. Then destroyed181demo resources from the isolated state. State is empty; live checks prove host terminated, namespace/folder/seven dashboards/IAM users/policy/secrets/buckets/Cognito/logging absent, shared EKS ACTIVE. KMS key is PendingDeletion for22October2026. Source248f699 and private consumer938ca42 preserve recreation inputs; private lifecycle runbook records next-demo steps.
<!-- SECTION:FINAL_SUMMARY:END -->
