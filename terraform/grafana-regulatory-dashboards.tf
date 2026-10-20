# Regulatory-only presentation and Knowledge Graph objects. Shared stack onboarding and
# Application Observability remain owned by their existing singleton resources.
locals {
  regulatory_agents_regex = join("|", [for role in sort(keys(local.regulatory_agent_teams)) : local.regulatory_service_names[role]])
  regulatory_rule_vars = {
    prefix        = var.regulatory_name
    metric_prefix = replace(var.regulatory_name, "-", "_")
    agents_re     = local.regulatory_agents_regex
    rule_re       = "${replace(var.regulatory_name, "-", "_")}_.*"
  }
  regulatory_recording_rules = yamldecode(templatefile("${path.module}/rules/regulatory-recording.yaml.tftpl", local.regulatory_rule_vars))
  regulatory_alert_rules     = yamldecode(templatefile("${path.module}/rules/regulatory-alerts.yaml.tftpl", local.regulatory_rule_vars))
  regulatory_dashboard_uid   = "${var.regulatory_name}-regulatory"
  regulatory_dashboard_url   = "${trimsuffix(data.grafana_cloud_stack.this.url, "/")}/d/${local.regulatory_dashboard_uid}"
  regulatory_dashboard_values = merge(local.regulatory_rule_vars, {
    ds_prom       = local.grafana.datasource_prom
    dashboard_uid = local.regulatory_dashboard_uid
    capture_mode  = var.regulatory_content_capture ? "enabled" : "disabled"
    quality_rules = "${local.regulatory_ids.rule_draft_quality}|${local.regulatory_ids.rule_review_quality}"
  })
  regulatory_dashboard_vars = {
    for k, v in local.regulatory_dashboard_values : k => trimsuffix(trimprefix(jsonencode(v), "\""), "\"")
  }
  regulatory_dashboard_spec = jsondecode(templatefile("${path.module}/dashboards/regulatory.json.tftpl", local.regulatory_dashboard_vars)).spec
}

resource "grafana_folder" "regulatory" {
  provider = grafana.stack
  count    = local.regulatory_enabled ? 1 : 0

  uid   = "${var.regulatory_name}-ai-observability"
  title = "${var.regulatory_name} regulatory authoring demo"
}

resource "grafana_apps_dashboard_dashboard_v2" "regulatory" {
  provider = grafana.stack
  count    = local.regulatory_enabled ? 1 : 0

  metadata {
    uid        = local.regulatory_dashboard_uid
    folder_uid = grafana_folder.regulatory[0].uid
  }
  spec {
    json = jsonencode(local.regulatory_dashboard_spec)
  }
}

resource "grafana_asserts_prom_rule_file" "regulatory_service_graph" {
  provider   = grafana.stack
  count      = local.regulatory_enabled && local.grafana_kg_enabled ? 1 : 0
  depends_on = [grafana_asserts_stack.this]

  name   = "${var.regulatory_name}-service-graph"
  active = true
  group {
    name     = "${var.regulatory_name}-calls"
    interval = "1m"
    rule {
      record = "asserts:relation:calls"
      expr = chomp(<<-EOT
        sum by (asserts_env, namespace, service, dst_namespace, dst_service) (
          label_replace(label_replace(label_replace(label_replace(
            rate(traces_service_graph_request_total{client_service_namespace="${var.regulatory_name}", server_service_namespace="${var.regulatory_name}", connection_type=""}[30m]),
          "dst_service", "$1", "server", "(.+)"),
          "dst_namespace", "$1", "server_service_namespace", "(.+)"),
          "service", "$1", "client", "(.+)"),
          "namespace", "$1", "client_service_namespace", "(.+)")
        )
      EOT
      )
    }
  }
}

resource "grafana_asserts_trace_config" "regulatory" {
  provider = grafana.stack
  count    = local.regulatory_enabled && local.grafana_kg_enabled ? 1 : 0

  name            = var.regulatory_name
  priority        = 9001
  default_config  = false
  data_source_uid = local.grafana.datasource_traces
  match {
    property = "asserts_entity_type"
    op       = "="
    values   = ["Service"]
  }
  match {
    property = "namespace"
    op       = "="
    values   = [var.regulatory_namespace]
  }
  entity_property_to_trace_label_mapping = {
    otel_service   = "resource.service.name"
    otel_namespace = "resource.service.namespace"
    namespace      = "resource.k8s.namespace.name"
    pod            = "resource.k8s.pod.name"
    container      = "resource.k8s.container.name"
  }
}
