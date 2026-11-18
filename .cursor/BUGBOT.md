# Grafana Cloud agent observability demo review

This repository demonstrates observability for in-app agents and coding agents. Changes
to `terraform/`, `charts/` or `agent-host/render/` must preserve the public module's
upgrade path. Keep the mappings in `terraform/moved.tf`. Keep in-app `use_cases` separate
from the shared gateway and coding-agent host. A change to rendered host user data can
replace the instance and lose gateway state. Check digest propagation and the offline
plans in `tools/check_use_case_plan.py` when reviewing upgrades.

Review `apps/dev-workstation/`, `apps/regulatory/` and guard paths for credential,
content-capture and policy isolation. Keep developer agent homes and Bedrock grants
scoped to the selected agent and allowed model profiles. Preserve the distinction between
metadata and full-content capture. Regulatory guard transport failures and untransformed
identifiers must stop before model input or content recording. Keep simulated review
states distinct from human approval and document where a local test cannot prove live
scoring.

`just check` already validates OpenTofu, offline plans, both Helm charts, shell scripts,
fixture scrubbing, and the Python and Node suites. Report an actionable gap those checks
miss. Use `just check` for local verification. Confirm images and cut a release only
through the documented release flow.
