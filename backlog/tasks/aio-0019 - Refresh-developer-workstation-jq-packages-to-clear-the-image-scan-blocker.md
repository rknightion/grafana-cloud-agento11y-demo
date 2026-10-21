---
id: AIO-0019
title: Refresh developer workstation jq packages to clear the image scan blocker
status: Done
assignee:
  - '@codex'
created_date: '2026-10-20T22:15:00Z'
updated_date: '2026-10-21T02:13:00Z'
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
- [x] #1 The developer workstation image installs a supported fixed jq and libjq package version and its HIGH/CRITICAL scan passes without a new suppression
- [x] #2 Image runtime checks and existing developer workstation tests pass; the resulting build is verified by exact-SHA image workflow evidence
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Inspect exact gateway/workstation image failure evidence and current distro package versions. Correct compatible package selection only where needed, prove build/runtime/scan, and land after review without weakening scanner gates.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Both gateway and workstation failed because cached apt layers retained jq/libjq1 deb12u2 despite a fixed deb12u3 candidate. Both Dockerfiles now install current jq/libjq1 and enforce a minimum deb12u3, accepting newer security versions. Final native arm64 builds and nonroot/network-none jq runtime smokes pass; workstation includes functional Codex/pi/agento11y and seeded codebase. Both image scans pass existing HIGH/CRITICAL ignore-unfixed policy with zero findings, no added suppression; jq has zero high/critical findings even including unfixed. Version check rejects vulnerable deb12u2 and accepts later deb12u4. Existing workstation/pi23 tests and full public repository gate pass. CodeRabbit completed coverage of both Dockerfiles with no findings. Await exact-SHA multiarchitecture workflow proof before terminal acceptance.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Gateway and workstation now install current jq/libjq1 and enforce deb12u3 minimum without new suppressions. Native builds, nonroot runtime/package checks,23workstation/pi tests and the full repository gate passed. CodeRabbit reviewed both Dockerfiles with no findings. Exact image workflow39530555516 for4d7381d5e9cdb8afb79fc1efc8e4aea6445d6611 passed both amd64/arm64 builds/scans and merge/sign/SBOM for both images; the entire image workflow completed successfully. Source CI39530843680 passed after public design-note privacy correction.
<!-- SECTION:FINAL_SUMMARY:END -->
