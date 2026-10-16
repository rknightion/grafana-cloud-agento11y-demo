---
id: AIO-0012
title: Prepare bounded customer-communications agent demo overlay
status: Done
assignee:
  - '@codex'
created_date: '2026-10-16 11:32'
updated_date: '2026-10-16 11:40'
labels: []
dependencies: []
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Prepare a rapid synthetic customer-communications workflow overlay on the running demo, using public product themes and real model/telemetry execution. Keep recipient identity and private deployment details out of the public repository.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Writing design and knowledge assistant workflows execute real bounded model calls and export identifiable conversations.
- [x] #2 Live telemetry and a usable demo navigation surface are verified before handoff.
- [x] #3 Overlay is bounded and does not disrupt the existing demo.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 just check
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Run a bounded private Kubernetes Job using the existing immutable agents image, service account and model/exporter configuration. Add three generic communications assistants with fictional insurance/banking fixtures, actual Bedrock calls and recorded retrieval tools. Verify exports, create a temporary companion Grafana dashboard and provide a short walkthrough. Customer-specific artifacts remain outside the public source.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Public product page reviewed; selected synthetic writing/design/knowledge workflows using fictional insurance/banking fixtures. Child produced bounded real Bedrock runner:3agents,12scenario variants,default10conversations30generations,18minute deadline. Root reviewed source and server-side validated Job/ConfigMap manifests. Reuses existing immutable image/IAM/Secret refs; no host replacement or source-image build. CodeRabbit review running before live execution; companion7panel dashboard prepared.

CodeRabbit completed review of runner:one minor suggests treating model fact-preservation as execution success. Left as a separate quality concern deliberately: completed records mean all3stages executed, not correctness; README/dashboard explicitly state this and show raw answers for review. No critical/major findings. Private just check passed, syntax/fixture/bounds checks passed. Smoke Job launched using existing image/IAM/exporter refs; bounded batch prepared. Companion dashboard queries pending real data.

Live smoke completed1conversation3generations; bounded batch completed10conversations30generations with0failures. Agent Observability search returns11conversations; inspected Spanish example confirms real outputs/token usage and Knowledge→Writing→Design parent DAG. All6dashboard data queries populated; rendered snapshot inspected, shortened legends after visual review. Dashboard uid communications-demo in existing folder; source and runtime job manifest private. No existing lab services changed. First smoke was suspended after non-numeric image-user config failure; replacement explicituid/gid1000 passed. Output cap increased190→400 after smoke truncation. Workload stops after batch; retained records ready for presentation.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Prepared and deployed synthetic writing/design/knowledge workflow overlay with real model calls and linked generations. Fourfictional product fixtures and10batchscenarios cover renewals, claims, rates, translations, mobile messaging and accessible templates. Batch30generations/10conversations completed without failures;11total conversations including smoke verified in Agent Observability. Companion7panel dashboard has all queries populated and visual verification passed. Existing demo untouched. CodeRabbit completed with1minor quality-validation suggestion deliberately kept distinct from execution completion; no major/critical findings. Private local gate passed, source syntax/bounds checks passed and actual runtime/API proof captured. Dashboard and bounded Job are temporary overlay resources; recreation/cleanup documented in private consumer.
<!-- SECTION:FINAL_SUMMARY:END -->
