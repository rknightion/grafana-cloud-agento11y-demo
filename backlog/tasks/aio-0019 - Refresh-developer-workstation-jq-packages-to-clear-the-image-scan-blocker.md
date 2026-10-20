---
id: AIO-0019
title: Refresh developer workstation jq packages to clear the image scan blocker
status: To Do
assignee: []
created_date: '2026-10-20T22:15:00Z'
labels: []
dependencies: []
references:
  - >-
    https://github.com/rknightion/grafana-cloud-agento11y-demo/security/code-scanning/19
priority: high
type: bug
ordinal: 42000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The existing dev-workstation image scan reports CVE-2026-32316 in jq/libjq1 1.6-2.1+deb12u2, with 1.6-2.1+deb12u3 listed as fixed. First code-scanning report predates the regulatory change (2026-10-19), and the image source is unchanged by that work. The all-images workflow exposes this separate publication blocker; do not suppress it through the existing ignore-unfixed setting or the agents-only braces exception.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The developer workstation image installs a supported fixed jq and libjq package version and its HIGH/CRITICAL scan passes without a new suppression
- [ ] #2 Image runtime checks and existing developer workstation tests pass; the resulting build is verified by exact-SHA image workflow evidence
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->
