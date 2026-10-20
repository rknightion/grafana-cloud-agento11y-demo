module "demo" {
  # Pin a release tag when consuming from git:
  # source = "github.com/rknightion/grafana-cloud-agento11y-demo//terraform?ref=vX.Y.Z"
  source = "../../terraform"

  providers = {
    aws           = aws
    kubernetes    = kubernetes
    helm          = helm
    grafana.cloud = grafana.cloud
    grafana.stack = grafana.stack
  }

  use_cases                      = var.use_cases
  regulatory_name                = var.regulatory_name
  regulatory_namespace           = var.regulatory_namespace
  regulatory_content_capture     = var.regulatory_content_capture
  regulatory_requests_per_minute = var.regulatory_requests_per_minute

  cluster_name             = var.cluster_name
  agent_host_enabled       = var.agent_host_subnet_id != null
  agent_host_subnet_id     = var.agent_host_subnet_id
  grafana_cloud_stack_slug = var.grafana_cloud_stack_slug

  bedrock_models                     = var.bedrock_models
  bedrock_invocation_logging_enabled = var.bedrock_invocation_logging_enabled
  frontend_observability_enabled     = var.frontend_observability_enabled
  manage_app_observability           = var.manage_app_observability

  traffic_enabled  = var.traffic_enabled
  deploy_workloads = var.deploy_workloads

  tags = var.tags
}
