---
id: AIO-0009
title: Improve existing dashboard category legends and sanitize IAM role labels
status: To Do
assignee: []
created_date: '2026-10-15 20:44'
labels: []
dependencies: []
ordinal: 25000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Rendered dashboard inspection found existing Gateway upstream and Bedrock region/stop-reason donuts use Value #A rather than category names. Bedrock IAM-role table can show a raw pi IAM ARN containing an account identifier. Keep screenshots private until labels are normalized. This is separate from the newly added multi-agent comparison views.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Gateway and Bedrock category panels show meaningful labels in rendered snapshots.
- [ ] #2 Bedrock caller table strips account identifiers for both assumed-role and IAM-user/role caller forms.
- [ ] #3 Queries preserve caller grouping and do not expose raw identifiers in display fields.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->
