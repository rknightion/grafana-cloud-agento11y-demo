---
id: AIO-0010
title: Expand coding-agent roster validate each developer and tear down demo
status: In Progress
assignee:
  - '@codex'
created_date: '2026-10-15 22:01'
updated_date: '2026-10-15 22:09'
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
- [ ] #1 Consumer defines five Claude Code, three Codex and three pi developers across all teams.
- [ ] #2 Each non-Claude developer completes a live session and appears in telemetry and dashboard grouping.
- [ ] #3 Saved configuration uses a workstation image with the fresh-home permissions fix.
- [ ] #4 Demo-only resources are destroyed after validation with shared cluster and unrelated workloads preserved.
- [ ] #5 Pi and Codex dashboards align with Claude Code styling and supported data; no unsupported empty panels remain.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
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
<!-- SECTION:NOTES:END -->
