# Offline: no cloud providers are called. Reserved example endpoints and synthetic account only.
mock_provider "aws" {
  mock_resource "aws_kinesis_firehose_delivery_stream" {
    defaults = { arn = "arn:aws:firehose:eu-west-2:000000000000:deliverystream/test" }
  }

  mock_resource "aws_iam_role" {
    defaults = { arn = "arn:aws:iam::000000000000:role/test" }
  }
  mock_resource "aws_secretsmanager_secret" {
    defaults = { arn = "arn:aws:secretsmanager:eu-west-2:000000000000:secret:test" }
  }
  mock_resource "aws_s3_bucket" {
    defaults = { arn = "arn:aws:s3:::demo-test" }
  }

  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
  mock_resource "aws_cognito_user_pool" {
    defaults = { id = "eu-west-2_test" }
  }

  mock_data "aws_caller_identity" {
    defaults = { account_id = "000000000000" }
  }
  mock_data "aws_region" {
    defaults = { region = "eu-west-2" }
  }
  mock_data "aws_partition" {
    defaults = { partition = "aws" }
  }
  mock_data "aws_ec2_instance_type" {
    defaults = { supported_architectures = ["arm64"] }
  }
  mock_resource "aws_bedrock_inference_profile" {
    defaults = { arn = "arn:aws:bedrock:eu-west-2:000000000000:application-inference-profile/test" }
  }
}
mock_provider "grafana" {
  alias = "cloud"
  mock_data "grafana_cloud_stack" {
    defaults = {
      id                 = "1"
      url                = "https://demo.example"
      region_slug        = "prod-gb-south-1"
      cluster_slug       = "prod-gb-south-1"
      prometheus_url     = "https://prometheus-prod-test-prod-gb-south-1.example"
      logs_url           = "https://logs.example"
      otlp_url           = "https://otlp.example/otlp"
      prometheus_user_id = 1
      logs_user_id       = 1
    }
  }
}
mock_provider "grafana" {
  alias = "stack"
}
mock_provider "kubernetes" {}
mock_provider "helm" {}
mock_provider "random" {}
mock_provider "tls" {}
mock_provider "cloudinit" {}

variables {
  cluster_name             = "demo-test"
  grafana_cloud_stack_slug = "demo-test"
  agent_host_subnet_id     = "subnet-test"
}

run "default_touchline" {
  command = plan
  assert {
    condition = (
      length(kubernetes_namespace_v1.this) == 1 &&
      length(kubernetes_secret_v1.grafana_otlp) == 1 &&
      length(kubernetes_secret_v1.agento11y) == 1 &&
      length(kubernetes_secret_v1.faro) == 1 &&
      length(kubernetes_secret_v1.experiments) == 1 &&
      length(aws_iam_role.agents) == 1 &&
      length(aws_eks_pod_identity_association.agents) == 1 &&
      length(helm_release.this) == 1 &&
      length(grafana_frontend_o11y_app.site) == 1
    )
    error_message = "The default must retain the Touchline namespace, secrets, Pod Identity, chart and Faro."
  }
  assert {
    condition     = contains(keys(output.dashboards), "agents") && length(kubernetes_namespace_v1.regulatory) == 0 && length(aws_iam_role.regulatory_agents) == 0 && length(aws_bedrock_inference_profile.regulatory_team_model) == 0 && output.chart_values_regulatory == null && length(grafana_folder.regulatory) == 0 && length(grafana_agento11y_evaluator.regulatory_number_grounding) == 0
    error_message = "The default must retain the Touchline agents dashboard."
  }
}

run "regulatory_only" {
  command = plan
  assert {
    condition = (
      length(kubernetes_namespace_v1.this) == 0 &&
      length(kubernetes_secret_v1.grafana_otlp) == 0 &&
      length(kubernetes_secret_v1.agento11y) == 0 &&
      length(kubernetes_secret_v1.faro) == 0 &&
      length(kubernetes_secret_v1.experiments) == 0 &&
      length(grafana_service_account.experiments) == 0 &&
      length(grafana_service_account_token.experiments) == 0 &&
      length(aws_iam_role.agents) == 0 &&
      length(aws_iam_role_policy.agents_bedrock) == 0 &&
      length(aws_eks_pod_identity_association.agents) == 0 &&
      length(helm_release.this) == 0 &&
      length(grafana_frontend_o11y_app.site) == 0 &&
      length(grafana_asserts_prom_rule_file.service_graph) == 0 &&
      length(grafana_asserts_trace_config.this) == 0 &&
      output.chart_values == null && output.agents_role_arn == null
    )
    error_message = "Regulatory-only must omit all Touchline workloads and their credentials, including with KG enabled."
  }
  assert {
    condition = alltrue([for n in [
      length(grafana_agento11y_evaluator.agents_quality),
      length(grafana_agento11y_evaluator.injected_tool_result),
      length(grafana_agento11y_evaluator.tool_result_markers),
      length(grafana_agento11y_evaluator.responsible_gambling),
      length(grafana_agento11y_evaluator.tool_result_grounded),
      length(grafana_agento11y_evaluator.response_not_empty),
      length(grafana_agento11y_evaluator.injection_resisted),
      length(grafana_agento11y_evaluator.session_helpfulness),
      length(grafana_agento11y_hook_rule.agents_redact_tool_pii),
      length(grafana_agento11y_hook_rule.agents_injected_tool_result),
      length(grafana_agento11y_evaluation_rule.agents_quality),
      length(grafana_agento11y_evaluation_rule.compliance_responsible_gambling),
      length(grafana_agento11y_evaluation_rule.specialists_tool_grounding),
      length(grafana_agento11y_evaluation_rule.news_injection_resistance),
      length(grafana_agento11y_evaluation_rule.orchestrator_session_helpfulness),
      length(grafana_agento11y_collection.rg_review),
      length(grafana_agento11y_rule_action.rg_review),
    ] : n == 0])
    error_message = "No Touchline-only evaluator, guard, evaluation rule or review collection may remain."
  }
  assert {
    condition = (
      length(aws_instance.agent_host) == 1 &&
      grafana_folder.this.uid == var.name &&
      grafana_agento11y_evaluator.pii_regex.evaluator_id != "" &&
      grafana_agento11y_evaluator.secrets_regex.evaluator_id != "" &&
      grafana_agento11y_evaluator.content_safety.evaluator_id != "" &&
      grafana_agento11y_evaluator.pii_judge.evaluator_id != "" &&
      grafana_agento11y_evaluator.secret_leak_response.evaluator_id != "" &&
      grafana_agento11y_evaluation_rule.claude_code.rule_id != "" &&
      contains(keys(output.dashboards), "gateway") &&
      contains(keys(output.dashboards), "coding-agents")
    )
    error_message = "The shared folder, host, dashboards and coding-agent protection must remain."
  }
  assert {
    condition = (
      !contains([for r in grafana_rule_group.recording.rule : r.uid], "${var.name}-rec-agent-cost") &&
      !contains([for r in grafana_rule_group.recording.rule : r.uid], "${var.name}-rec-agents-p95") &&
      contains([for r in grafana_rule_group.recording.rule : r.uid], "${var.name}-rec-guard") &&
      !contains([for r in grafana_rule_group.alerts.rule : r.uid], "${var.name}-al-guard") &&
      !contains([for r in grafana_rule_group.alerts.rule : r.uid], "${var.name}-al-agents-cost") &&
      contains([for r in grafana_rule_group.alerts.rule : r.uid], "${var.name}-al-guard-deny") &&
      alltrue(flatten([for d in grafana_apps_dashboard_dashboard_v2.this : [for link in jsondecode(d.spec.json).links : try(link.url, "") != "/d/${var.name}-agents"]]))
    )
    error_message = "Filter Touchline rules and navigation links inside shared Grafana objects, keeping shared guard monitoring."
  }
  variables {
    use_cases               = ["regulatory"]
    knowledge_graph_enabled = true
  }
  assert {
    condition     = !contains(keys(output.dashboards), "agents")
    error_message = "Regulatory-only must omit the Touchline agents dashboard."
  }
  assert {
    condition = (
      length(kubernetes_namespace_v1.regulatory) == 1 &&
      length(aws_iam_role.regulatory_agents) == 1 &&
      length(aws_bedrock_inference_profile.regulatory_team_model) == 3 * length(var.bedrock_models) &&
      length(kubernetes_secret_v1.regulatory_grafana_otlp) == 1 &&
      length(kubernetes_secret_v1.regulatory_agento11y) == 1 &&
      length(kubernetes_secret_v1.regulatory_experiments) == 1 &&
      length(helm_release.regulatory) == 1 &&
      length(grafana_folder.regulatory) == 1 &&
      length(grafana_agento11y_evaluator.regulatory_number_grounding) == 1 &&
      length(grafana_agento11y_hook_rule.regulatory_patient_identifiers) == 1 &&
      grafana_asserts_trace_config.regulatory[0].priority == 9001 &&
      contains(keys(output.dashboards), "regulatory") &&
      contains([for rule in grafana_rule_group.alerts.rule : rule.uid], "dossier-al-reg-guard")
    )
    error_message = "Regulatory selection must create its isolated app, profiles, protection, presentation and trace mapping."
  }
}

run "both" {
  command = plan
  variables {
    use_cases = ["touchline", "regulatory"]
    images    = { digests = { regulatory = "sha256:fixture" } }
  }
  assert {
    condition = (
      length(helm_release.this) == 1 &&
      length(local.regulatory_team_models) == 3 * length(var.bedrock_models) &&
      toset(keys(local.regulatory_service_names)) == toset(["orchestrator", "source", "drafter", "reviewer", "readability", "loadgen"]) &&
      !contains(keys(local.chart_values.images.digests), "regulatory") &&
      length(local.team_models) == length(var.teams) * length(var.bedrock_models)
    )
    error_message = "Both use cases retain Touchline, isolate regulatory teams and exclude regulatory digests from the Touchline chart."
  }
}

run "regulatory_without_host_or_touchline_teams" {
  command = plan
  variables {
    use_cases            = ["regulatory"]
    agent_host_enabled   = false
    teams                = ["writers"]
    team_model_allowlist = {}
    developers           = []
  }
  assert {
    condition     = length(aws_instance.agent_host) == 0 && length(helm_release.this) == 0 && keys(local.team_models) == ["writers.haiku", "writers.sonnet"]
    error_message = "Regulatory-only must not demand Touchline teams or deploy the disabled host."
  }
}

run "empty_selection" {
  command = plan
  variables { use_cases = [] }
  expect_failures = [var.use_cases]
}
run "unsupported_selection" {
  command = plan
  variables { use_cases = ["pharma"] }
  expect_failures = [var.use_cases]
}
run "overlapping_prefix" {
  command = plan
  variables {
    use_cases       = ["regulatory"]
    regulatory_name = "touchline-dossier"
  }
  expect_failures = [terraform_data.team_checks]
}
run "duplicate_namespace" {
  command = plan
  variables {
    use_cases            = ["regulatory"]
    regulatory_namespace = "touchline"
  }
  expect_failures = [terraform_data.team_checks]
}
run "unsupported_model" {
  command = plan
  variables {
    use_cases               = ["regulatory"]
    regulatory_agent_models = { orchestrator = "unknown", source = "haiku", drafter = "sonnet", reviewer = "sonnet", readability = "haiku" }
  }
  expect_failures = [terraform_data.team_checks]
}
run "negative_rate" {
  command = plan
  variables { regulatory_requests_per_minute = -1 }
  expect_failures = [var.regulatory_requests_per_minute]
}

# Existing Touchline users may have their own names and model keys. Disabled regulatory defaults
# must not make those formerly valid configurations require regulatory input overrides.
run "legacy_touchline_custom_inputs" {
  command = plan
  variables {
    name                 = "dossier"
    namespace            = "dossier"
    bedrock_models       = { small = "eu.anthropic.claude-haiku-4-5-20251001-v1:0" }
    agent_models         = { orchestrator = "small", news = "small", odds = "small", editorial = "small", compliance = "small" }
    gateway_models       = ["small"]
    judge_model          = "small"
    team_model_allowlist = {}
  }
  assert {
    condition     = length(helm_release.this) == 1 && length(local.regulatory_team_models) == 0
    error_message = "Disabled regulatory defaults must preserve existing customized Touchline configurations."
  }
}

run "regulatory_external_release" {
  command = plan
  variables {
    use_cases                  = ["regulatory"]
    deploy_workloads           = false
    traffic_enabled            = false
    regulatory_content_capture = false
    regulatory_name            = "document-demo"
    regulatory_namespace       = "document-runtime"
  }
  assert {
    condition = (
      length(helm_release.regulatory) == 0 &&
      length(kubernetes_namespace_v1.regulatory) == 1 &&
      kubernetes_namespace_v1.regulatory[0].metadata[0].name == "document-runtime" &&
      local.regulatory_chart_values.namespace == "document-demo" &&
      !local.regulatory_chart_values.traffic.enabled &&
      !local.regulatory_chart_values.contentCapture &&
      output.chart_values_regulatory != null &&
      local.regulatory_service_accounts.agents == "document-demo-agents"
    )
    error_message = "External deployment must retain isolated credentials and values while respecting pause/capture and namespace separation."
  }
}
