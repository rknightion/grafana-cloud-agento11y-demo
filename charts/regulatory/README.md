# Regulatory demo chart

Version: 0.5.0 <!-- x-release-please-version -->

Fictional ICF/CSR authoring with five agents, a load generator, a scheduled experiments job and
namespace-scoped Grafana Alloy. Review states simulate a queue; this is not human approval or
GxP validation. There is no site, Redis or Faro component.

Terraform creates the namespace, existing Secrets and EKS Pod Identity association. Install this
chart with its `chart_values_regulatory` output. Do not install it alongside Terraform's Helm
release; set `deploy_workloads=false` when another controller owns the release.

```sh
helm upgrade --install dossier ./charts/regulatory --namespace dossier --values regulatory-values.yaml
```

| Value | Default | Meaning |
| --- | --- | --- |
| `nameOverride` | `dossier` | Resource prefix, aligned with Terraform `regulatory_name`. |
| `namespace` | `dossier` | Telemetry `service.namespace`, independent of the Helm release namespace. |
| `images.registry` / `images.namePrefix` | `ghcr.io/rknightion` / `gc-agento11y-` | Regulatory image location. |
| `images.tag` | `0.5.0` | Shared release tag. <!-- x-release-please-version --> |
| `images.digests.regulatory` | unset | Optional immutable SHA-256 pin; other digest keys are rejected. |
| `serviceAccounts` | `dossier-{agents,loadgen,experiments}` | Separate Pod Identity agents, unprivileged loadgen and Lease experiments identities. |
| `secrets.grafanaOtlp` | `dossier-grafana-otlp` | Existing Secret: `endpoint`, `username`, `password`. |
| `secrets.agento11y` | `dossier-agento11y` | Existing Secret: `endpoint`, `tenant_id`, `token`. |
| `secrets.experiments` | `dossier-experiments` | Existing Secret: `grafana_url`, `token`. |
| `aws.region` | `eu-west-1` | Bedrock region. |
| `agents` | Five roles | `orchestrator`, `source`, `drafter`, `reviewer`, `readability`, each with team/model settings. |
| `agentVersion` | `v1` | Prompt-set governance label. |
| `contentCapture` | `true` | Full guarded content capture; false retains metadata and in-app scores. |
| `traffic.enabled` | `true` | False scales loadgen to zero and suspends experiments. |
| `traffic.requestsPerMinute` | `2` | Synthetic document requests per minute. |
| `traffic.experimentsSchedule` | `37 * * * *` | Scheduled section-prompt/guard-policy experiments. |
| `alloy.enabled` | `true` | Namespace-scoped OTLP and pod-log collection. |

Pod Identity uses its own projected token. Agents and loadgen do not mount the general Kubernetes
API token. Experiments can create Leases and get/update/patch their single named Lease; Alloy can
read only pods, pod logs and ReplicaSets in the release namespace. All containers have resource
bounds and non-root security contexts. Secrets contain synthetic-demo credentials only; never use
real patient or regulated data. Metadata mode omits free-form content while grounding and reading
grade remain available. With Alloy disabled, configure an alternative collector before generating
traffic: the default app exporter points at the chart's Alloy Service.
