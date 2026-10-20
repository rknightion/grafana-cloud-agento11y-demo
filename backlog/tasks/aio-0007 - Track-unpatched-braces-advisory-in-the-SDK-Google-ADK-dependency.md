---
id: AIO-0007
title: Track unpatched braces advisory in the SDK Google ADK dependency
status: Parked
assignee:
  - '@codex'
created_date: '2026-10-15 17:52'
updated_date: '2026-10-20T21:58:00Z'
labels: []
dependencies: []
priority: medium
type: task
ordinal: 23000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
GitHub Dependabot alert 10 identifies braces <=3.0.3 through @grafana/agento11y 0.13.0 -> @google/adk -> MikroORM -> globby -> fast-glob -> micromatch. No patched version is reported. Determine whether the vulnerable parser is reachable from this demo and adopt an upstream compatible fix when available; do not change scanner policy merely to make publication green.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Reachability and upstream fix availability are documented from current evidence.
- [x] #2 A compatible remediation is validated or an exact upstream resume condition is recorded.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Identify the exact image-scan findings and reachability of the SDK dependency chain. Fix compatible patched dependencies where available; retain an explicit upstream blocker where no supported patch exists.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Live npm registry latest braces 3.0.3 remains affected; GHSA-vfj7-8cjw-p6xm has no first_patched_version. Trivy filesystem scan reports only CVE-2026-93687 high in agents dependency tree. Demo imports SDK root and experiments, not google-adk; runtime import trace resolved 77 modules and no braces/Google ADK/MikroORM/globby/micromatch. Dated risk exception decision requested from maintainer; no ignore applied yet.

Upstream has no patched braces release. Maintainer decision pending: dated single-advisory exception until 2026-11-15, hold full deployment, or remove the unused dependency chain through a separate packaging change. No scanner exception has been applied. Exact resume: obtain disposition, implement only the approved path, then publish the agents image with all other scan gates unchanged.

Maintainer approved the proposed exception on 2026-10-15: CVE-2026-93687 only, agents image only, expires 2026-11-15. Keep every other scanner gate unchanged; deploy after successful publication.

Approved exception implemented in apps/agents/.trivyignore.yaml, exact installed package path and CVE, expires 2026-11-15. Wired only to agents image matrix entry. ARM64 publication scan has passed with other findings still enforced; final release publication remains in progress. Upstream remediation remains open: remove exception when a compatible fix ships or before expiry.

Actual Trivy image scan with approved exception passes; same image with valid YAML expiry set to yesterday fails exit 1 and reports exactly CVE-2026-93687 in braces. Expiry and package-path filtering verified. YAML/CI wiring is declarative, so CodeRabbit skipped under policy; parse/scrub and image scans used.

Full just check passed on v0.5.0. Approved suppression passes both main-branch image architecture builds; expiry negative check reports the advisory again. Keep this task parked after rollout until upstream patch availability or expiry triggers removal/reassessment.

Approved exception is deployed and verified; upstream remediation is still pending. Resume before2026-11-15 to remove it with a compatible upstream fix or request a new explicit disposition. No other advisory suppression was added.

Release v0.5.0 publication and deployment completed with the approved exception; verified expiry prevents suppression after its date. Full release CI and all image jobs succeeded. No automatic renewal; revisit upstream fix before2026-11-15.

2026-10-20 regulatory build: the separate local regulatory image also contains braces 3.0.3 and Trivy reports exactly CVE-2026-93687 HIGH with no fixed version. No regulatory exception was added or reused. Existing approval remains agents image only. Regulatory source integration continues, but publication requires an upstream-compatible remediation or a separate maintainer disposition.
<!-- SECTION:NOTES:END -->
