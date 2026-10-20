---
title: Cost
description: What grafana-cloud-agento11y-demo costs to run, and how to cap it.
---

# Cost

Rough on-demand estimates for the defaults in `eu-west-1`, with 730 hours a month. Check the AWS
pricing calculator for your region before relying on them.

| Item | Default | Approximate cost |
|---|---|---|
| EKS control plane | one cluster | USD 0.10/hour, about USD 73/month |
| EKS Auto Mode compute | agents, site, Redis, Alloy (about 0.5 vCPU and 1.9 GiB requested) | one or two small nodes plus the Auto Mode management fee, roughly USD 50 to 110/month |
| Agent host | `t4g.xlarge`, 60 GB gp3 | about USD 110/month |
| NAT gateway | one, from `examples/eks-auto-mode` | about USD 35/month plus USD 0.048 per GB processed |
| Secrets Manager, Firehose, metric stream, Cognito (5 users), CloudWatch | | a few USD/month |
| Bedrock, in-app agents | load generator at 2 questions/minute, its own daily budget guard (chart value `loadgen.dailyBudgetUsd`, USD 5/day by default) | usually well under the guard; a typical question costs under one US cent |
| Bedrock, Claude Code developers | 5 developers, a session every 20 minutes each, USD 0.30 hard budget per session | capped by the gateway: USD 20/day per developer by default, USD 5/day for the trading team, USD 2/day for one platform developer; so at most about USD 52/day |
| Bedrock, optional Codex/pi developers | opt-in personas, one session per interval | additional spend outside gateway caps; local session estimates can overshoot an in-flight turn |
| Bedrock, LLM-judge evaluations | 10 to 25% sampling on Haiku | small next to the traffic itself |
| Grafana Cloud | | see below |

Fixed infrastructure is roughly USD 280 to 340 a month. Bedrock is the variable part and, with
traffic on all day, usually the biggest.

## Non-Claude developer budgets

The default five-person roster remains Claude Code. Adding Codex or pi adds Bedrock traffic
which never enters the gateway spend ledger or its organization, team and user caps. The existing
USD 52/day estimate above covers only the default Claude roster; it is not a total cap for a mixed
roster. Budget for the extra personas separately and monitor actual Bedrock billing.

The shared runner carries one conversation budget across follow-ups using normalized usage. Pi
checks priced usage after a model response and stops subsequent work when it reaches the remaining
budget. Codex estimates usage only when a whole CLI turn finishes; that turn may contain several
model and tool calls and can exceed the remaining budget before follow-ups stop. Neither provides
a server-enforced daily ceiling. Timeouts and maximum turns bound activity, not exact dollar cost.

Pi's first supported profile is EU Haiku 4.5 with explicit input, output and cache prices; unknown
profiles fail closed at render time instead of reporting zero cost. Codex is limited to
`openai.gpt-5.6-luna` in `us-east-1`. Changing model or routing region needs a fresh pricing check.
Agent Observability's Coding agents view compares estimates across agents; the gateway SQL
dashboard only accounts for Claude calls.

## Kill switch

`traffic_enabled = false` stops the developer sessions, the load generator and the experiment
schedule without removing anything; Bedrock spend then drops to near zero while the dashboards
keep their history. This knob lives in the agent-host secret, not the host's user data, so the
host picks it up within 5 minutes without being replaced. `agent_host_enabled = false` removes the
host.

## Grafana Cloud

A free stack is enough to try the demo for a short time, but full content capture (prompts,
responses and tool content in logs) and Claude Code's per-session metric series grow quickly. For
a demo you leave running for days, use a paid or trial stack and watch the stack's usage
dashboards. Agent Observability, Frontend Observability and Application Observability are billed
under their own usage terms.

## See also

- [Teardown](teardown.md) to remove everything, or pause instead
- [Security](security.md) for what content capture actually turns on

## Regulatory workload

The optional regulatory chart adds five agent deployments, loadgen and its own Alloy. Running
both use cases adds that compute to Touchline; a regulatory-only installation omits Touchline's
site and Redis but keeps the host and shared infrastructure unless separately disabled. The
Touchline estimates above are not a measured regulatory cost forecast.

A document-section request fans out to source, drafting and review work, with an additional
readability path for ICF. Model choice, input length, request rate and experiment/evaluator runs
therefore determine spend. `regulatory_requests_per_minute` controls arrivals, not a dollar cap.
The Touchline loadgen's daily guard and gateway developer caps do not cap regulatory traffic.
Monitor the regulatory token/cost panels as estimates and check actual AWS billing. Full capture
also adds log and Agent Observability storage; turning it off removes content scoring inputs
but retains app grounding/readability metrics.

`traffic_enabled = false` stops new scheduled regulatory traffic along with the other workloads;
in-flight requests/jobs can finish and manual requests still work. Removing `regulatory` from
`use_cases` removes that workload and its scoped infrastructure. See
[Regulatory authoring](regulatory.md) and [Teardown](teardown.md).
