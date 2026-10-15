---
id: AIO-0007
title: Track unpatched braces advisory in the SDK Google ADK dependency
status: Parked
assignee:
  - '@codex'
created_date: '2026-10-15 17:52'
updated_date: '2026-10-15 18:18'
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
- [ ] #1 Reachability and upstream fix availability are documented from current evidence.
- [ ] #2 A compatible remediation is validated or an exact upstream resume condition is recorded.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Identify the exact image-scan findings and reachability of the SDK dependency chain. Fix compatible patched dependencies where available; retain an explicit upstream blocker where no supported patch exists.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Live npm registry latest braces 3.0.3 remains affected; GHSA-vfj7-8cjw-p6xm has no first_patched_version. Trivy filesystem scan reports only CVE-2026-93687 high in agents dependency tree. Demo imports SDK root and experiments, not google-adk; runtime import trace resolved 77 modules and no braces/Google ADK/MikroORM/globby/micromatch. Dated risk exception decision requested from maintainer; no ignore applied yet.

Upstream has no patched braces release. Maintainer decision pending: dated single-advisory exception until 2026-11-15, hold full deployment, or remove the unused dependency chain through a separate packaging change. No scanner exception has been applied. Exact resume: obtain disposition, implement only the approved path, then publish the agents image with all other scan gates unchanged.
<!-- SECTION:NOTES:END -->
