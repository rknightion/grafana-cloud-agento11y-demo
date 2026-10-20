# Permanent upgrade mappings from the pre-use_cases module. Keep for consumers on older tags.

moved {
  from = kubernetes_namespace_v1.this
  to   = kubernetes_namespace_v1.this[0]
}

moved {
  from = kubernetes_secret_v1.grafana_otlp
  to   = kubernetes_secret_v1.grafana_otlp[0]
}

moved {
  from = kubernetes_secret_v1.agento11y
  to   = kubernetes_secret_v1.agento11y[0]
}

moved {
  from = kubernetes_secret_v1.faro
  to   = kubernetes_secret_v1.faro[0]
}

moved {
  from = kubernetes_secret_v1.experiments
  to   = kubernetes_secret_v1.experiments[0]
}

moved {
  from = grafana_service_account.experiments
  to   = grafana_service_account.experiments[0]
}

moved {
  from = grafana_service_account_token.experiments
  to   = grafana_service_account_token.experiments[0]
}

moved {
  from = aws_iam_role.agents
  to   = aws_iam_role.agents[0]
}

moved {
  from = aws_iam_role_policy.agents_bedrock
  to   = aws_iam_role_policy.agents_bedrock[0]
}

moved {
  from = aws_eks_pod_identity_association.agents
  to   = aws_eks_pod_identity_association.agents[0]
}

moved {
  from = grafana_agento11y_evaluator.agents_quality
  to   = grafana_agento11y_evaluator.agents_quality[0]
}

moved {
  from = grafana_agento11y_evaluator.injected_tool_result
  to   = grafana_agento11y_evaluator.injected_tool_result[0]
}

moved {
  from = grafana_agento11y_evaluator.tool_result_markers
  to   = grafana_agento11y_evaluator.tool_result_markers[0]
}

moved {
  from = grafana_agento11y_evaluator.responsible_gambling
  to   = grafana_agento11y_evaluator.responsible_gambling[0]
}

moved {
  from = grafana_agento11y_evaluator.tool_result_grounded
  to   = grafana_agento11y_evaluator.tool_result_grounded[0]
}

moved {
  from = grafana_agento11y_evaluator.response_not_empty
  to   = grafana_agento11y_evaluator.response_not_empty[0]
}

moved {
  from = grafana_agento11y_evaluator.injection_resisted
  to   = grafana_agento11y_evaluator.injection_resisted[0]
}

moved {
  from = grafana_agento11y_evaluator.session_helpfulness
  to   = grafana_agento11y_evaluator.session_helpfulness[0]
}

moved {
  from = grafana_agento11y_hook_rule.agents_redact_tool_pii
  to   = grafana_agento11y_hook_rule.agents_redact_tool_pii[0]
}

moved {
  from = grafana_agento11y_hook_rule.agents_injected_tool_result
  to   = grafana_agento11y_hook_rule.agents_injected_tool_result[0]
}

moved {
  from = grafana_agento11y_evaluation_rule.agents_quality
  to   = grafana_agento11y_evaluation_rule.agents_quality[0]
}

moved {
  from = grafana_agento11y_evaluation_rule.compliance_responsible_gambling
  to   = grafana_agento11y_evaluation_rule.compliance_responsible_gambling[0]
}

moved {
  from = grafana_agento11y_evaluation_rule.specialists_tool_grounding
  to   = grafana_agento11y_evaluation_rule.specialists_tool_grounding[0]
}

moved {
  from = grafana_agento11y_evaluation_rule.news_injection_resistance
  to   = grafana_agento11y_evaluation_rule.news_injection_resistance[0]
}

moved {
  from = grafana_agento11y_evaluation_rule.orchestrator_session_helpfulness
  to   = grafana_agento11y_evaluation_rule.orchestrator_session_helpfulness[0]
}

moved {
  from = grafana_agento11y_collection.rg_review
  to   = grafana_agento11y_collection.rg_review[0]
}

moved {
  from = grafana_agento11y_rule_action.rg_review
  to   = grafana_agento11y_rule_action.rg_review[0]
}

moved {
  from = data.aws_iam_policy_document.agents_assume
  to   = data.aws_iam_policy_document.agents_assume[0]
}
