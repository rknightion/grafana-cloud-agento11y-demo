# Loop: grafana-cloud-agento11y-demo
tier: guarded
gate: just check
ci-required: ci-success
grafana-stack: none
tracker: github
landing: pr

Issues are public: no customer name, account id, tenant or stack id, hostname, address, email or
credential in any issue, pull request or doc. Run `just` with stdin from `/dev/null`. `just check`
needs `tofu`, `helm`, `tflint`, `kubeconform`, `shellcheck`, Node and Python; CI runs the same gate.

The tracker working model is `~/repos/agent-docs/docs/github-tracker.md` (maintainers only).

## Queue

- The queue is `just tracker queue`: open issues at Project Status Ready on the rknightion Project.
- A charter selects work by labels (`type:task`, `type:bug`, `type:feature`, `needs-owner`,
  `needs-triage`) and Project fields (Status, Priority, Effort, Lane). Never queue a `needs-owner` or
  `needs-triage` issue. Parked work sits at Status Needs input with the `parked` label.
- Only the root writes issues and the Project, through `just tracker`. A lane returns the status and
  the AC ticks it wants.
- A queue row names the issue as `#N`. A legacy board id (`AIO-0001`) resolves with `just issue <ID>`;
  `.github/tracker/id-map.json` is the map. A bare `#N` below the first imported issue is a pull
  request or the Renovate dashboard.

## Credentials

- None held by the loop. The lab deployment that consumes this module is a separate private
  consumer; no lane applies Terraform from here.

## Traps

- A lab deployment is out of reach of a lane: a task whose acceptance needs a live deployment is
  Parked with what was built, what could not be observed and the exact resume condition.
- Never commit a customer or lab identifier: `tools/scrub_check.py` with the private denylist gates
  every commit and CI. Missing denylist means the local check skips with a warning, so a worktree
  needs it (untracked, `.scrub-denylist`) before a commit.
- The docs under `docs/` publish through the docs hub: no tracker history there; it lives in
  `.github/tracker/history/`.
