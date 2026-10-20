# Flux regulatory release

Reuse the repository's existing Flux GitRepository in `flux-system`. Apply Terraform with
`use_cases=["regulatory"]` (or both use cases) and `deploy_workloads=false`, then create the
`dossier-values` ConfigMap from `chart_values_regulatory` in the Terraform-created namespace.
Apply this directory's HelmRelease. Match its namespace and release prefix to your Terraform
inputs. Values contain profile ARNs; keep the populated ConfigMap out of this public repository.
The chart references existing Secrets and never creates credentials.
