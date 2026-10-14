---
id: AIO-0005
title: 'Add Codex, pi, Copilot and Cursor developers to the agent host'
status: To Do
assignee: []
created_date: '2026-10-14 11:57'
updated_date: '2026-10-14 11:58'
labels: []
dependencies: []
references:
  - >-
    https://grafana.com/docs/grafana-cloud/observe-and-act/agent-observability/guides/instrument-coding-agents/
  - 'https://github.com/grafana/agento11y/tree/main/plugins'
documentation:
  - backlog/docs/doc-0002 - Research-Codex-pi-Copilot-and-Cursor-developers.md
priority: medium
type: feature
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The agent host only runs Claude Code developers, so the demo shows Agent Observability for one coding agent. Grafana ships agento11y integrations for Codex, Copilot CLI, pi and Cursor, and the app has a built-in Coding agents view that compares agents side by side. This parent groups the work to run those agents next to Claude Code.

Research, canonical sources and per-agent facts: doc-0002 (read it first). Canonical sources are the Grafana guide https://grafana.com/docs/grafana-cloud/observe-and-act/agent-observability/guides/instrument-coding-agents/ and plugins/<agent>/README.md in grafana/agento11y at the pinned tag.

Decisions already taken by the maintainer (do not re-open):
- Scope: Codex and pi are implemented. Copilot and Cursor each start with a go/no-go spike that the maintainer signs off before any implementation.
- Model access: a scoped Bedrock credential (new IAM principal) in the agent-host secret. No loop budgets, no AWS Budgets alarm, no data-residency constraint (a US region for OpenAI-on-Bedrock is fine). The Claude apps gateway is not used by the new agents. Developer containers still never reach IMDS.
- Hosting: the same agent host. All render.py, bundle and seam changes ship in one release with one planned host replacement.

Ordering and ownership: AIO-0005.01 owns render.py, SEAM.md, variables.tf and the shared session scripts. AIO-0005.05 owns terraform/grafana-agento11y.tf. The agent tasks add their parts through those seams. Copilot or Cursor work that lands after the rollout causes a second host replacement; batch it if both go ahead.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Codex and pi developers run unattended next to the Claude Code developers, and their sessions appear in the Agent Observability Coding agents view with agent, user, team, model and tokens
- [ ] #2 Guards deny the same classes of destructive and secret-reading tool calls for Codex and pi as for Claude Code, and docs state each agent's guard gaps
- [ ] #3 Copilot and Cursor each have a recorded go/no-go decision signed off by the maintainer, and are implemented or closed accordingly
- [ ] #4 The rollout replaced the host once, and Claude Code traffic, dashboards and guards behave as before
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->
