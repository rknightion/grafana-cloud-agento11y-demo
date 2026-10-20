---
title: Regulatory Helm reference
description: Values and deployment boundary for the separate regulatory authoring chart.
---

# Regulatory Helm reference

The regulatory workload uses its own chart and image. The [chart reference](https://github.com/rknightion/grafana-cloud-agento11y-demo/blob/main/charts/regulatory/README.md)
lists values, defaults, service accounts, Secrets, telemetry and traffic controls.
Terraform supplies `chart_values_regulatory`; use it as the values file when deploying with Helm,
Flux or Argo CD and set `deploy_workloads=false` so two controllers do not own the same release.

`nameOverride` is the regulatory resource prefix. The chart's `namespace` value is the telemetry
`service.namespace` and equals Terraform `regulatory_name`. Helm's `--namespace` selects the actual
Kubernetes namespace and equals `regulatory_namespace`; these may differ.

Only `images.digests.regulatory` is accepted by this chart. It does not accept Touchline or host
image digests. The experiments job and load generator are disabled by `traffic.enabled=false`.
For the full operator procedure and capture boundary, see [regulatory authoring](regulatory.md).
