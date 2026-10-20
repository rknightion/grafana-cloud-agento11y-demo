#!/usr/bin/env python3
"""Offline default-plan compatibility against the pre-use_cases module.

Run after `tofu -chdir=terraform init -backend=false`. The fixture is generated
explicitly from a Git revision, never refreshed by the normal check. Providers
are mocked with schema-derived deterministic computed values; no cloud API runs.

Generate the original proof once with --generate-baseline <BASELINE>. After an
intentional module/release change, explicitly refresh with --accept-current
"reason for the planned change" and review the fixture diff. Refreshes retain
the original baseline identity and record the previous fixture hash and Git HEAD.
The normal gate never writes the fixture.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tools/fixtures/default-use-case-plan.json"
BASELINE = "8be4a4c82e337a9388d2070ae06c3d030a997dab"

# Syntax-valid values for computed fields consumed by module expressions.
OVERRIDES = {
    "aws_kinesis_firehose_delivery_stream": {"arn": "arn:aws:firehose:eu-west-2:000000000000:deliverystream/test"},
    "aws_iam_role": {"arn": "arn:aws:iam::000000000000:role/test"},
    "aws_secretsmanager_secret": {"arn": "arn:aws:secretsmanager:eu-west-2:000000000000:secret:test"},
    "aws_s3_bucket": {"arn": "arn:aws:s3:::demo-test"},
    "aws_iam_policy_document": {"json": '{"Version":"2012-10-17","Statement":[]}'},
    "aws_cognito_user_pool": {"id": "eu-west-2_test"},
    "aws_caller_identity": {"account_id": "000000000000"},
    "aws_region": {"region": "eu-west-2"},
    "aws_partition": {"partition": "aws"},
    "aws_ec2_instance_type": {"supported_architectures": ["arm64"]},
    "aws_bedrock_inference_profile": {"arn": "arn:aws:bedrock:eu-west-2:000000000000:application-inference-profile/test"},
    "grafana_cloud_stack": {
        "id": "1", "url": "https://demo.example", "region_slug": "prod-gb-south-1",
        "cluster_slug": "prod-gb-south-1", "prometheus_user_id": 1, "logs_user_id": 1,
        "prometheus_url": "https://prometheus-prod-test-prod-gb-south-1.example",
        "logs_url": "https://logs.example", "otlp_url": "https://otlp.example/otlp",
    },
}


def command(args, cwd):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(f"{' '.join(args)} failed:\n{result.stdout[-12000:]}\n{result.stderr[-4000:]}")
    return result.stdout


def default_value(kind):
    if kind == "string":
        return "mockvalue"
    if kind == "number":
        return 1
    if kind == "bool":
        return False
    if isinstance(kind, list):
        tag, inner = kind
        if tag in ("list", "set", "tuple"):
            return [] if tag != "tuple" else [default_value(t) for t in inner]
        if tag == "map":
            return {}
        if tag == "object":
            return {k: default_value(v) for k, v in inner.items()}
    raise ValueError(f"Unsupported provider type: {kind}")


def computed_defaults(block, configured=None):
    values = {}
    for name, attr in block.get("attributes", {}).items():
        if attr.get("computed") and (not attr.get("optional") or (configured is not None and name not in configured)):
            if "type" in attr:
                values[name] = default_value(attr["type"])
            else:
                nested = attr["nested_type"]
                item = {k: default_value(v["type"]) for k, v in nested["attributes"].items()}
                values[name] = item if nested["nesting_mode"] == "single" else []
    if configured is not None:
        for name, nested in block.get("block_types", {}).items():
            if name in configured and any(a.get("computed") for a in nested["block"].get("attributes", {}).values()):
                expressions = configured[name]
                if nested["nesting_mode"] in ("single", "group"):
                    expressions = [expressions]
                if not isinstance(expressions, list):
                    raise ValueError(f"Unsupported block configuration for {name}")
                # Mock block defaults apply to every instance; reject differing shapes.
                shapes = [set(item) for item in expressions]
                if shapes and any(shape != shapes[0] for shape in shapes):
                    raise ValueError(f"Mixed configured block shapes for {name}")
                if expressions:
                    item = computed_defaults(nested["block"], expressions[0])
                    if item:
                        values[name] = item
    return values


def mock_test(schema, module, configuration=None):
    source = "\n".join(p.read_text() for p in module.glob("*.tf"))
    used = {mode: set(re.findall(rf'\b{mode}\s+"([^"]+)"', source)) for mode in ("resource", "data")}
    found = {mode: set() for mode in used}
    chunks = []
    for provider, details in schema["provider_schemas"].items():
        name = provider.rsplit("/", 1)[-1]
        if provider.startswith("terraform.io/"):
            found["resource"].update(used["resource"] & details.get("resource_schemas", {}).keys())
            found["data"].update(used["data"] & details.get("data_source_schemas", {}).keys())
            continue
        bodies = []
        for mode, key in (("resource", "resource_schemas"), ("data", "data_source_schemas")):
            for typ in sorted(used[mode] & details.get(key, {}).keys()):
                found[mode].add(typ)
                values = computed_defaults(details[key][typ]["block"])
                values.update({k: v for k, v in OVERRIDES.get(typ, {}).items() if k in details[key][typ]["block"].get("attributes", {})})
                bodies.append(f'mock_{mode} "{typ}" {{\n defaults = {json.dumps(values)}\n}}')
        for alias in (["cloud", "stack"] if name == "grafana" else [None]):
            chunks.append(f'mock_provider "{name}" {{\n' + (f'alias = "{alias}"\n' if alias else "") + "\n".join(bodies) + "\n}")
    if found != used:
        raise ValueError(f"Missing provider schema coverage: { {k: sorted(used[k] - found[k]) for k in used} }")
    if configuration is not None:
        providers = schema["provider_schemas"]
        for resource in configuration["root_module"]["resources"]:
            typ = resource["type"]
            mode = "data" if resource["mode"] == "data" else "resource"
            key = "data_source_schemas" if mode == "data" else "resource_schemas"
            matches = [p[key][typ]["block"] for p in providers.values() if typ in p.get(key, {})]
            if typ == "terraform_data":
                continue
            if len(matches) != 1:
                raise ValueError(f"Ambiguous schema for {typ}")
            values = computed_defaults(matches[0], resource.get("expressions", {}))
            values.update({k: v for k, v in OVERRIDES.get(typ, {}).items() if k in values})
            chunks.append(f'override_{mode} {{\n target = {resource["address"]}\n values = {json.dumps(values)}\n}}')
    chunks.append('variables {\n cluster_name = "demo-test"\n grafana_cloud_stack_slug = "demo-test"\n agent_host_subnet_id = "subnet-test"\n}\nrun "compatibility" { command = plan }')
    if configuration is not None:
        chunks.append('run "regulatory_digest" {\n command = plan\n variables { images = { digests = { regulatory = "sha256:fixture" } } }\n}')
    return "\n".join(chunks)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def planned_hashes(checkout, cache, check_regulatory_digest=True):
    module = checkout / "terraform"
    data = module / ".terraform"
    data.mkdir(exist_ok=True)
    (data / "providers").symlink_to(cache)
    schema = json.loads(command(["tofu", "providers", "schema", "-json"], module))
    tests = module / "compatibility-tests"
    tests.mkdir()
    (tests / "default.tftest.hcl").write_text(mock_test(schema, module))
    bootstrap = command(["tofu", "test", "-test-directory=compatibility-tests", "-json", "-verbose"], module)
    bootstrap_plans = [e["test_plan"] for line in bootstrap.splitlines() if (e := json.loads(line)).get("type") == "test_plan"]
    if len(bootstrap_plans) != 1:
        raise ValueError("Expected one bootstrap plan for configuration discovery")
    (tests / "default.tftest.hcl").write_text(mock_test(schema, module, bootstrap_plans[0]["configuration"]))
    events = command(["tofu", "test", "-test-directory=compatibility-tests", "-json", "-verbose"], module)
    events = [json.loads(line) for line in events.splitlines() if line.strip()]
    plans = [e["test_plan"] for e in events if e.get("type") == "test_plan"]
    if len(plans) != 2 or any(plan.get("errored") for plan in plans):
        raise ValueError("Expected exactly two successful compatibility plans")
    if not any(e.get("type") == "test_summary" and e["test_summary"].get("passed") == 2 for e in events):
        raise ValueError("Mock plan test did not report a passing run")
    plan = plans[0]
    host = "aws_instance.agent_host[0]"
    default_hosts = {r["address"]: r["values"] for r in plan["planned_values"]["root_module"]["resources"]}
    digest_hosts = {r["address"]: r["values"] for r in plans[1]["planned_values"]["root_module"]["resources"]}
    if host not in default_hosts or host not in digest_hosts:
        raise ValueError("Agent host must be enabled for the compatibility proof")
    if not default_hosts[host].get("user_data_base64") or (check_regulatory_digest and default_hosts[host]["user_data_base64"] != digest_hosts[host].get("user_data_base64")):
        raise ValueError("Regulatory digest changed default agent-host user_data_base64")
    resources = plan["planned_values"]["root_module"]["resources"]
    if not resources or plan["planned_values"]["root_module"].get("child_modules"):
        raise ValueError("Expected nonempty root resource coverage; child module coverage must be added explicitly")
    unknowns = {r["address"]: r["change"].get("after_unknown", {}) for r in plan["resource_changes"]}
    result = {r["address"]: digest({"values": r["values"], "unknown": unknowns[r["address"]]}) for r in resources}
    if len(result) != len(resources):
        raise ValueError("Duplicate planned address")
    return {"resources": result, "outputs": {k: digest(v) for k, v in plan["planned_values"]["outputs"].items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate-baseline", metavar="GIT_SHA", help="explicitly generate fixture from the pre-gating revision")
    parser.add_argument("--accept-current", metavar="REASON", help="explicitly accept intentional current-plan changes; review the fixture diff")
    args = parser.parse_args()
    if args.generate_baseline and args.accept_current:
        parser.error("Generation and refresh are mutually exclusive")
    if args.accept_current is not None and not args.accept_current.strip():
        parser.error("Refresh requires a nonempty reason")
    cache = (ROOT / "terraform/.terraform/providers").resolve()
    if not cache.is_dir():
        raise ValueError("Initialize locked Terraform providers first (tofu init -backend=false)")
    with tempfile.TemporaryDirectory(prefix="use-case-plan-") as temporary:
        checkout = Path(temporary)
        if args.generate_baseline:
            if args.generate_baseline != BASELINE:
                raise ValueError(f"Baseline must be the pre-gating revision {BASELINE}")
            archive = subprocess.run(["git", "archive", BASELINE, "terraform", "agent-host", "charts"], cwd=ROOT, capture_output=True, check=True, timeout=30)
            subprocess.run(["tar", "-x", "-C", temporary], input=archive.stdout, check=True, timeout=30)
        else:
            for directory in ("terraform", "agent-host", "charts"):
                shutil.copytree(ROOT / directory, checkout / directory, ignore=shutil.ignore_patterns(".terraform", "*.tfstate*"))
        actual = planned_hashes(checkout, cache, check_regulatory_digest=not args.generate_baseline)
    if args.generate_baseline:
        FIXTURE.parent.mkdir(exist_ok=True)
        FIXTURE.write_text(json.dumps({"baseline_commit": BASELINE, **actual}, indent=2, sort_keys=True) + "\n")
        print(f"Generated {len(actual['resources'])} baseline resource hashes from {BASELINE}")
        return
    if args.accept_current:
        previous = json.loads(FIXTURE.read_text())
        if previous["baseline_commit"] != BASELINE:
            raise ValueError("Invalid original baseline identity")
        history = previous.get("refreshes", [])
        history.append({"reason": args.accept_current, "git_head": command(["git", "rev-parse", "HEAD"], ROOT).strip(), "previous_fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest()})
        FIXTURE.write_text(json.dumps({"baseline_commit": BASELINE, "refreshes": history, **actual}, indent=2, sort_keys=True) + "\n")
        print("Accepted current planned values; review the fixture diff and refresh reason")
        return
    expected = json.loads(FIXTURE.read_text())
    refreshes = expected.pop("refreshes", [])
    if expected.pop("baseline_commit") != BASELINE or not expected.get("resources"):
        raise ValueError("Invalid baseline identity or empty coverage")
    moves = (ROOT / "terraform/moved.tf").read_text()
    for old, new in re.findall(r'moved\s*\{\s*from\s*=\s*(\S+)\s+to\s*=\s*(\S+)\s*\}', moves):
        for address in list(expected["resources"]):
            if address == old:
                replacement = new + address[len(old):]
                if replacement in expected["resources"]:
                    raise ValueError(f"Move collision: {replacement}")
                expected["resources"][replacement] = expected["resources"].pop(address)
    differences = []
    for section in ("resources", "outputs"):
        for key in sorted(expected[section].keys() | actual[section].keys()):
            if expected[section].get(key) != actual[section].get(key):
                differences.append(f"{section}: {key}")
    if differences:
        raise ValueError("Default plan differs from baseline:\n" + "\n".join(differences))
    identity = f"refreshed fixture ({len(refreshes)} explicit refreshes, original {BASELINE})" if refreshes else BASELINE
    print(f"Default plan matches {identity}: {len(actual['resources'])} resources and {len(actual['outputs'])} outputs (moved addresses accounted for)")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, subprocess.SubprocessError, OSError) as error:
        raise SystemExit(str(error)) from error
