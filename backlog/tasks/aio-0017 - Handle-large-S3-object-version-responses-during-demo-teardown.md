---
id: AIO-0017
title: Handle large S3 object-version responses during demo teardown
status: To Do
assignee: []
created_date: '2026-10-16 13:17'
labels: []
dependencies: []
ordinal: 33000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Demo destroy failed while emptying its invocation-log bucket: AWS provider ListObjectVersions response parsing returned bufio.Scanner token too long despite HTTP200. All other resources were removed. Paginated AWS API cleanup of the exact bucket succeeded, then a fresh one-resource destroy plan completed. Investigate provider remediation or a bounded cleanup path for repeatable lab destruction.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Teardown of an invocation-log bucket with representative object keys succeeds without manual recovery.
- [ ] #2 Cleanup remains restricted to resources owned by the isolated demo state.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->
