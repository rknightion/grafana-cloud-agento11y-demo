# Direct Bedrock credentials for the isolated non-Claude developer containers. No login profile,
# instance role, marketplace subscription, secrets or other AWS service access is granted here.

variable "codex_bedrock" {
  description = "Exact Mantle model and request region for Codex developers. Used only when an enabled agent host has a Codex developer. Model access must already exist in the account."
  type = object({
    model  = string
    region = string
  })
  default = {
    model  = "openai.gpt-5.6-luna"
    region = "us-east-1"
  }

  validation {
    condition = (
      can(regex("^openai\\.[a-z0-9][a-z0-9.-]*$", var.codex_bedrock.model)) &&
      can(regex("^[a-z]{2}(-[a-z]+)+-[0-9]+$", var.codex_bedrock.region))
    )
    error_message = "codex_bedrock must name one exact OpenAI model and AWS region, without wildcards."
  }
}

locals {
  developer_bedrock_agents = var.agent_host_enabled ? toset([
    for d in var.developers : d.agent if contains(["codex", "pi"], d.agent)
  ]) : toset([])

  # A shared pi principal has the union of the selected pi teams' allowlists. It never receives
  # profiles for teams with no pi developer, nor models excluded by that team's allowlist.
  developer_pi_teams = toset([for d in var.developers : d.team if d.agent == "pi"])
  developer_pi_profiles = {
    for key, pair in local.team_models : key => pair
    if contains(local.developer_pi_teams, pair.team) &&
    contains(var.gateway_models, pair.model) &&
    contains(lookup(var.team_model_allowlist, pair.team, var.gateway_models), pair.model)
  }
  developer_pi_profile_arns = [
    for key in keys(local.developer_pi_profiles) : aws_bedrock_inference_profile.team_model[key].arn
  ]
  developer_pi_foundation_model_arns = distinct(flatten([
    for pair in values(local.developer_pi_profiles) : data.aws_bedrock_inference_profile.source[pair.model].models[*].model_arn
  ]))

  # Root integrates this map into the existing agent-host secret. No value belongs in user data,
  # compose environment, an output or a generated documentation artifact.
  developer_bedrock_credentials = {
    for agent, key in aws_iam_access_key.developer_bedrock : agent => {
      access_key_id     = key.id
      secret_access_key = key.secret
      region            = agent == "codex" ? var.codex_bedrock.region : local.aws_region
    }
  }
}

resource "aws_iam_user" "developer_bedrock" {
  for_each = local.developer_bedrock_agents

  name = "${local.prefix}-developer-${each.key}-bedrock"
  tags = var.tags
}

data "aws_iam_policy_document" "developer_codex_bedrock" {
  count = contains(local.developer_bedrock_agents, "codex") ? 1 : 0

  statement {
    sid     = "InvokeSelectedMantleModel"
    effect  = "Allow"
    actions = ["bedrock-mantle:CreateInference"]
    # Mantle authorizes inference on projects, not foundation-model ARNs. The client chooses
    # the default project; no project ID is invented here. Model and request region are exact.
    resources = ["arn:${local.aws_partition}:bedrock-mantle:${var.codex_bedrock.region}:${local.aws_account_id}:project/*"]

    condition {
      test     = "StringEquals"
      variable = "bedrock-mantle:Model"
      values   = [var.codex_bedrock.model]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.codex_bedrock.region]
    }
  }
}

data "aws_iam_policy_document" "developer_pi_bedrock" {
  count = contains(local.developer_bedrock_agents, "pi") ? 1 : 0

  statement {
    sid       = "InvokeSelectedPiProfiles"
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = local.developer_pi_profile_arns

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [local.aws_region]
    }
  }

  statement {
    sid       = "InvokePiBackingModelsThroughProfiles"
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = local.developer_pi_foundation_model_arns

    condition {
      test     = "ArnEquals"
      variable = "bedrock:InferenceProfileArn"
      values   = local.developer_pi_profile_arns
    }
  }

  lifecycle {
    precondition {
      condition = length(local.developer_pi_profile_arns) > 0 && alltrue([
        for team in local.developer_pi_teams : anytrue([
          for pair in values(local.developer_pi_profiles) : pair.team == team
        ])
      ])
      error_message = "Every pi developer team requires at least one existing gateway model in its allowlist."
    }
  }
}

resource "aws_iam_user_policy" "developer_bedrock" {
  for_each = local.developer_bedrock_agents

  name = "${local.prefix}-developer-${each.key}-bedrock"
  user = aws_iam_user.developer_bedrock[each.key].name
  policy = (
    each.key == "codex" ? data.aws_iam_policy_document.developer_codex_bedrock[0].json :
    data.aws_iam_policy_document.developer_pi_bedrock[0].json
  )
}

resource "aws_iam_access_key" "developer_bedrock" {
  for_each = local.developer_bedrock_agents

  user = aws_iam_user.developer_bedrock[each.key].name

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [aws_iam_user_policy.developer_bedrock]
}
