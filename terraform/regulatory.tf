# The regulatory workload is isolated from the shared gateway and coding-agent team matrix.
# Selecting it never changes the agent-host role, secret or user data.

locals {
  regulatory_chart_path = "${path.module}/../charts/regulatory"
  regulatory_service_accounts = {
    agents      = "${var.regulatory_name}-agents"
    loadgen     = "${var.regulatory_name}-loadgen"
    experiments = "${var.regulatory_name}-experiments"
  }
  regulatory_model_profile_arns = { for key, profile in aws_bedrock_inference_profile.regulatory_team_model : key => profile.arn }
  regulatory_profile_arns       = values(local.regulatory_model_profile_arns)
  regulatory_foundation_model_arns = distinct(flatten([
    for pair in values(local.regulatory_team_models) : data.aws_bedrock_inference_profile.source[pair.model].models[*].model_arn
  ]))
}

resource "aws_bedrock_inference_profile" "regulatory_team_model" {
  for_each = local.regulatory_team_models

  name        = "${var.regulatory_name}-${each.value.team}-${each.value.model}"
  description = "${var.regulatory_name} ${each.value.team} team ${each.value.model} copied from ${each.value.source_profile}"
  model_source {
    copy_from = data.aws_bedrock_inference_profile.source[each.value.model].inference_profile_arn
  }
  tags = merge(var.tags, {
    Team  = each.value.team
    Model = each.value.model
  })
}

data "aws_iam_policy_document" "regulatory_agents_assume" {
  count = local.regulatory_enabled ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole", "sts:TagSession"]
    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.aws_account_id]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/eks-cluster-name"
      values   = [var.cluster_name]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/kubernetes-namespace"
      values   = [var.regulatory_namespace]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/kubernetes-service-account"
      values   = [local.regulatory_service_accounts.agents]
    }
  }
}

data "aws_iam_policy_document" "regulatory_bedrock_invoke" {
  count = local.regulatory_enabled ? 1 : 0

  statement {
    sid    = "InvokeRegulatoryProfiles"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "bedrock:CountTokens",
      "bedrock:GetInferenceProfile",
    ]
    resources = local.regulatory_profile_arns
  }
  statement {
    sid    = "InvokeBackingModelsThroughRegulatoryProfiles"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = local.regulatory_foundation_model_arns
    condition {
      test     = "ArnEquals"
      variable = "bedrock:InferenceProfileArn"
      values   = local.regulatory_profile_arns
    }
  }
  statement {
    sid       = "CountTokens"
    effect    = "Allow"
    actions   = ["bedrock:CountTokens"]
    resources = local.regulatory_foundation_model_arns
  }
}

resource "aws_iam_role" "regulatory_agents" {
  count = local.regulatory_enabled ? 1 : 0

  name               = "${var.regulatory_name}-agents"
  description        = "Assumed through EKS Pod Identity by ${var.regulatory_namespace}/${local.regulatory_service_accounts.agents}"
  assume_role_policy = data.aws_iam_policy_document.regulatory_agents_assume[0].json
  tags               = var.tags
}

resource "aws_iam_role_policy" "regulatory_agents_bedrock" {
  count = local.regulatory_enabled ? 1 : 0

  name   = "${var.regulatory_name}-agents-bedrock"
  role   = aws_iam_role.regulatory_agents[0].id
  policy = data.aws_iam_policy_document.regulatory_bedrock_invoke[0].json
}

resource "aws_eks_pod_identity_association" "regulatory_agents" {
  count = local.regulatory_enabled ? 1 : 0

  cluster_name    = var.cluster_name
  namespace       = var.regulatory_namespace
  service_account = local.regulatory_service_accounts.agents
  role_arn        = aws_iam_role.regulatory_agents[0].arn
  tags            = var.tags
}

resource "kubernetes_namespace_v1" "regulatory" {
  count = local.regulatory_enabled ? 1 : 0

  metadata {
    name = var.regulatory_namespace
    labels = {
      "app.kubernetes.io/part-of" = var.regulatory_name
    }
  }
}

resource "kubernetes_secret_v1" "regulatory_grafana_otlp" {
  count = local.regulatory_enabled ? 1 : 0

  metadata {
    name      = "${var.regulatory_name}-grafana-otlp"
    namespace = kubernetes_namespace_v1.regulatory[0].metadata[0].name
  }
  data = {
    endpoint = local.grafana_ingest.otlp_endpoint
    username = local.grafana_ingest.otlp_username
    password = local.grafana_ingest.otlp_token
  }
}

resource "kubernetes_secret_v1" "regulatory_agento11y" {
  count = local.regulatory_enabled ? 1 : 0

  metadata {
    name      = "${var.regulatory_name}-agento11y"
    namespace = kubernetes_namespace_v1.regulatory[0].metadata[0].name
  }
  data = {
    endpoint  = local.grafana_ingest.agento11y_endpoint
    tenant_id = local.grafana_ingest.agento11y_tenant
    token     = local.grafana_ingest.agento11y_token
  }
}

# Agent Observability experiment writes require an Admin stack service account.
resource "grafana_service_account" "regulatory_experiments" {
  count = local.regulatory_enabled ? 1 : 0

  provider = grafana.stack
  name     = "${var.regulatory_name}-experiments"
  role     = "Admin"
}

resource "grafana_service_account_token" "regulatory_experiments" {
  count = local.regulatory_enabled ? 1 : 0

  provider           = grafana.stack
  name               = "${var.regulatory_name}-experiments"
  service_account_id = grafana_service_account.regulatory_experiments[0].id
}

resource "kubernetes_secret_v1" "regulatory_experiments" {
  count = local.regulatory_enabled ? 1 : 0

  metadata {
    name      = "${var.regulatory_name}-experiments"
    namespace = kubernetes_namespace_v1.regulatory[0].metadata[0].name
  }
  data = {
    grafana_url = local.grafana_stack.url
    token       = grafana_service_account_token.regulatory_experiments[0].key
  }
}

locals {
  regulatory_chart_values = local.regulatory_enabled ? {
    nameOverride = var.regulatory_name
    # Telemetry uses the resource prefix even when the Kubernetes namespace differs.
    namespace = var.regulatory_name
    images = {
      registry   = var.images.registry
      namePrefix = var.images.name_prefix
      tag        = var.images.tag
      digests    = { for key, digest in var.images.digests : key => digest if key == "regulatory" }
      pullSecret = var.images.pull_secret == null ? "" : var.images.pull_secret
    }
    serviceAccounts = local.regulatory_service_accounts
    secrets = {
      grafanaOtlp = kubernetes_secret_v1.regulatory_grafana_otlp[0].metadata[0].name
      agento11y   = kubernetes_secret_v1.regulatory_agento11y[0].metadata[0].name
      experiments = kubernetes_secret_v1.regulatory_experiments[0].metadata[0].name
    }
    aws = { region = local.aws_region }
    agents = { for role, team in local.regulatory_agent_teams : role => {
      team            = team
      modelKey        = var.regulatory_agent_models[role]
      modelName       = lookup(var.bedrock_models, var.regulatory_agent_models[role], "")
      modelProfileArn = lookup(local.regulatory_model_profile_arns, "${team}.${var.regulatory_agent_models[role]}", "")
    } }
    contentCapture = var.regulatory_content_capture
    traffic = {
      enabled           = var.traffic_enabled
      requestsPerMinute = var.regulatory_requests_per_minute
    }
  } : null
}

resource "helm_release" "regulatory" {
  count = var.deploy_workloads && local.regulatory_enabled ? 1 : 0

  name      = var.regulatory_name
  namespace = kubernetes_namespace_v1.regulatory[0].metadata[0].name
  chart     = local.regulatory_chart_path
  values = [yamlencode(merge(local.regulatory_chart_values, {
    chartDigest = sha1(join("", [for file in sort(fileset(local.regulatory_chart_path, "**")) : filesha1("${local.regulatory_chart_path}/${file}")]))
  }))]
  wait    = true
  timeout = 600

  depends_on = [aws_eks_pod_identity_association.regulatory_agents, aws_iam_role_policy.regulatory_agents_bedrock]
}
