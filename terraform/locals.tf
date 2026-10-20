# Shared names and derived maps. Frozen seam: every lane builds on these, none redefines them.

locals {
  prefix = var.name

  use_cases          = var.use_cases
  touchline_enabled  = contains(local.use_cases, "touchline")
  regulatory_enabled = contains(local.use_cases, "regulatory")

  # Independent of the coding-agent host and its gateway team/profile contract.
  regulatory_ids = { for key, suffix in {
    evaluator_number_grounding   = "number_grounding"
    evaluator_citation_grounding = "citation_grounding"
    evaluator_reading_grade      = "reading_grade"
    evaluator_unsupported_claims = "unsupported_claims"
    evaluator_review_outcome     = "review_outcome"
    guard_patient_identifiers    = "patient_identifiers"
    guard_source_note_injection  = "source_note_injection"
    rule_draft_quality           = "draft_quality"
    rule_review_quality          = "review_quality"
  } : key => "${replace(var.regulatory_name, "-", "_")}_${suffix}" }
  regulatory_service_names = { for role in ["orchestrator", "source", "drafter", "reviewer", "readability", "loadgen"] : role => "${var.regulatory_name}-${role}" }
  regulatory_agent_teams = {
    orchestrator = "medical-writing"
    source       = "clinical-science"
    drafter      = "medical-writing"
    reviewer     = "regulatory-affairs"
    readability  = "medical-writing"
  }
  regulatory_team_models = { for pair in setproduct(distinct(values(local.regulatory_agent_teams)), keys(var.bedrock_models)) :
    "${pair[0]}.${pair[1]}" => {
      team           = pair[0]
      model          = pair[1]
      source_profile = var.bedrock_models[pair[1]]
    } if local.regulatory_enabled
  }

  service_names = {
    orchestrator = "${var.name}-orchestrator"
    news         = "${var.name}-news"
    odds         = "${var.name}-odds"
    editorial    = "${var.name}-editorial"
    compliance   = "${var.name}-compliance"
    loadgen      = "${var.name}-loadgen"
    site_api     = "${var.name}-site-api"
    site_web     = "${var.name}-site-web"
    gateway      = "${var.name}-gateway"
    agent_host   = "${var.name}-agent-host"
  }

  # In-app agent => owning team (drives which application inference profile each agent calls).
  agent_teams = {
    orchestrator = "platform"
    news         = "newsroom"
    odds         = "trading"
    editorial    = "newsroom"
    compliance   = "platform"
  }

  service_accounts = {
    agents      = "${var.name}-agents"
    site        = "${var.name}-site"
    loadgen     = "${var.name}-loadgen"
    experiments = "${var.name}-experiments"
  }

  developers = { for d in var.developers : d.name => merge(d, {
    email = "${d.name}@${var.developer_email_domain}"
  }) }

  claude_developers = { for name, d in local.developers : name => d if d.agent == "claude-code" }

  teams = toset(var.teams)

  # "<team>.<model key>" => { team, model, source_profile } for per-team application inference profiles.
  team_models = { for pair in setproduct(var.teams, keys(var.bedrock_models)) :
    "${pair[0]}.${pair[1]}" => {
      team           = pair[0]
      model          = pair[1]
      source_profile = var.bedrock_models[pair[1]]
    }
  }

  grafana = {
    folder_uid        = var.name
    spend_datasource  = "${var.name}-gateway-spend"
    contact_point     = "${var.name}-null"
    metric_prefix     = replace(var.name, "-", "_")
    demo_label        = "${replace(var.name, "-", "_")}_demo"
    dashboards        = [for d in ["agents", "bedrock", "claude-code", "gateway", "codex", "pi", "coding-agents"] : d if d != "agents" || local.touchline_enabled]
    guard_prefix      = replace(var.name, "-", "_")
    datasource_prom   = "grafanacloud-prom"
    datasource_logs   = "grafanacloud-logs"
    datasource_traces = "grafanacloud-traces"
  }

  chart_path = "${path.module}/../charts/touchline"
}

# The AWS side and kubernetes.tf read Grafana ingest details through this one local.
locals {
  grafana_ingest = local.grafana_ingest_l4
}
