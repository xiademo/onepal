#!/usr/bin/env python3
"""OnePal Readiness Center Tests - Tasks 16-20.

Usage: py tests/test_readiness_centers.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
SCRIPT = PROJECT_ROOT / "scripts" / "readiness_center.py"

SCHEMAS = [
    "knowledge_node.schema.json",
    "knowledge_edge.schema.json",
    "knowledge_state.schema.json",
    "boundary_candidate.schema.json",
    "model_router.schema.json",
    "cost_event.schema.json",
    "mcp_server_profile.schema.json",
    "tool_trust_policy.schema.json",
]

passed = 0
failed = 0


def test(name, ok, msg=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")
        if msg:
            for line in str(msg).split("\n")[:3]:
                print(f"         {line}")
    return ok


def run_cmd(cmd, timeout=60):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace")


def parse(result):
    try:
        return json.loads((result.stdout or "").strip())
    except json.JSONDecodeError:
        return {"parse_error": (result.stdout or "")[:300], "stderr": (result.stderr or "")[:300]}


def load_jsonl(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def paths(tmpdir):
    return {
        "workflows": tmpdir / "automation" / "workflows.jsonl",
        "runs": tmpdir / "automation" / "runs.jsonl",
        "skills": tmpdir / "capabilities" / "skills.jsonl",
        "skill_reviews": tmpdir / "capabilities" / "skill_reviews.jsonl",
        "nodes": tmpdir / "kg" / "nodes.jsonl",
        "edges": tmpdir / "kg" / "edges.jsonl",
        "boundaries": tmpdir / "kg" / "boundaries.jsonl",
        "state": tmpdir / "kg" / "state.jsonl",
        "routes": tmpdir / "model" / "routes.jsonl",
        "costs": tmpdir / "model" / "costs.jsonl",
        "mcp_profiles": tmpdir / "mcp" / "profiles.jsonl",
        "tool_policies": tmpdir / "mcp" / "policies.jsonl",
        "audit": tmpdir / "logs" / "readiness_audit.jsonl",
    }


def path_args(p):
    return [
        "--workflows-log", str(p["workflows"]),
        "--runs-log", str(p["runs"]),
        "--skills-log", str(p["skills"]),
        "--skill-reviews-log", str(p["skill_reviews"]),
        "--nodes-log", str(p["nodes"]),
        "--edges-log", str(p["edges"]),
        "--boundaries-log", str(p["boundaries"]),
        "--state-log", str(p["state"]),
        "--model-routes-log", str(p["routes"]),
        "--cost-events-log", str(p["costs"]),
        "--mcp-profiles-log", str(p["mcp_profiles"]),
        "--tool-policies-log", str(p["tool_policies"]),
        "--audit-log", str(p["audit"]),
    ]


def test_T1():
    print("\n--- T1: readiness schemas registered ---")
    registry = json.loads((PROJECT_ROOT / "schemas" / "registry.json").read_text(encoding="utf-8"))
    ids = {entry["schema_id"] for entry in registry.get("schemas", [])}
    test("T1: readiness_center.py exists", SCRIPT.exists())
    for sid in SCHEMAS:
        test(f"T1-{sid}: schema registered", (PROJECT_ROOT / "schemas" / "core" / sid).exists() and sid in ids)


def test_T2(tmpdir):
    print("\n--- T2: automation workflow disabled and trigger preflight only ---")
    p = paths(tmpdir / "t2")
    wf = parse(run_cmd([PY, str(SCRIPT), "workflow-create", "--name", "Daily local review", "--action-refs", "read_file"] + path_args(p))).get("workflow", {})
    run = parse(run_cmd([PY, str(SCRIPT), "workflow-trigger", "--workflow-id", wf.get("workflow_id", "")] + path_args(p))).get("run", {})
    ok = wf.get("enabled") is False and wf.get("approval_required") is True and run.get("status") == "preflight" and "not_executed" in run.get("output_refs", [])
    return test("T2: workflow trigger does not execute action", ok, f"wf={wf} run={run}")


def test_T3(tmpdir):
    print("\n--- T3: skill candidate disabled and review does not enable ---")
    p = paths(tmpdir / "t3")
    skill = parse(run_cmd([PY, str(SCRIPT), "skill-candidate", "--name", "Local parser", "--description", "parse local docs"] + path_args(p))).get("skill", {})
    review = parse(run_cmd([PY, str(SCRIPT), "skill-review", "--skill-id", skill.get("skill_id", ""), "--result", "passed"] + path_args(p))).get("review", {})
    ok = skill.get("enabled") is False and skill.get("sandbox_status") == "not_run" and review.get("enabled_after_review") is False
    return test("T3: skill remains disabled", ok, f"skill={skill} review={review}")


def test_T4(tmpdir):
    print("\n--- T4: knowledge graph candidates and RAG disabled state ---")
    p = paths(tmpdir / "t4")
    n1 = parse(run_cmd([PY, str(SCRIPT), "kg-node", "--label", "Memory governance", "--source-refs", "memqr_1"] + path_args(p))).get("node", {})
    n2 = parse(run_cmd([PY, str(SCRIPT), "kg-node", "--label", "Change request", "--source-refs", "memchg_1"] + path_args(p))).get("node", {})
    edge = parse(run_cmd([PY, str(SCRIPT), "kg-edge", "--from-node-ref", n1.get("node_id", ""), "--to-node-ref", n2.get("node_id", ""), "--relation", "relates_to"] + path_args(p))).get("edge", {})
    boundary = parse(run_cmd([PY, str(SCRIPT), "boundary-create", "--summary", "Need user confirmation for durable memory"] + path_args(p))).get("boundary", {})
    state = parse(run_cmd([PY, str(SCRIPT), "kg-state"] + path_args(p))).get("knowledge_state", {})
    ok = edge.get("status") == "candidate" and boundary.get("status") == "candidate" and state.get("rag_enabled") is False and state.get("node_count") == 2
    return test("T4: KG records candidate and RAG disabled", ok, f"state={state}")


def test_T5(tmpdir):
    print("\n--- T5: model route LiteLLM disabled and cost event local ---")
    p = paths(tmpdir / "t5")
    route = parse(run_cmd([PY, str(SCRIPT), "model-route", "--task-type", "code_review", "--default-model", "local/manual"] + path_args(p))).get("route", {})
    cost = parse(run_cmd([PY, str(SCRIPT), "cost-event", "--task-ref", "task_1", "--model", "local/manual", "--estimated-cost-usd", "0"] + path_args(p))).get("cost_event", {})
    ok = route.get("litellm_enabled") is False and route.get("status") == "draft" and cost.get("estimated_cost_usd") == 0
    return test("T5: model/cost readiness local only", ok, f"route={route} cost={cost}")


def test_T6(tmpdir):
    print("\n--- T6: MCP and tool trust disabled by default ---")
    p = paths(tmpdir / "t6")
    profile = parse(run_cmd([PY, str(SCRIPT), "mcp-profile", "--name", "local-test-server"] + path_args(p))).get("profile", {})
    policy = parse(run_cmd([PY, str(SCRIPT), "tool-policy", "--tool-ref", "tool_local"] + path_args(p))).get("policy", {})
    ok = profile.get("enabled") is False and profile.get("write_actions_allowed") is False and profile.get("approval_required") is True and policy.get("write_allowed") is False and policy.get("approval_required") is True
    return test("T6: MCP/tool write disabled", ok, f"profile={profile} policy={policy}")


def test_T7(tmpdir):
    print("\n--- T7: secret-like content rejected ---")
    p = paths(tmpdir / "t7")
    result = run_cmd([PY, str(SCRIPT), "workflow-create", "--name", "token=abcdefghijklmnopqrstuvwxyz"] + path_args(p))
    ok = result.returncode != 0 and load_jsonl(p["workflows"]) == []
    return test("T7: secret workflow rejected", ok, f"exit={result.returncode}")


def test_T8():
    print("\n--- T8: static safety and gitignore ---")
    text = SCRIPT.read_text(encoding="utf-8")
    stripped = "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))
    no_shell_network = "shell=True" not in stripped and "http://" not in stripped and "https://" not in stripped
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    ignored = all(item in gitignore for item in [
        "automation/**/*.jsonl",
        "capabilities/**/*.jsonl",
        "knowledge_graph/**/*.jsonl",
        "model_cost/**/*.jsonl",
        "mcp/**/*.jsonl",
        "logs/readiness_audit.jsonl",
    ])
    test("T8: no shell/network in readiness script", no_shell_network)
    test("T8b: readiness runtime data gitignored", ignored)


def main():
    print("=" * 60)
    print("OnePal Readiness Center Tests")
    print("=" * 60)
    test_T1()
    with tempfile.TemporaryDirectory(prefix="onepal_readiness_test_") as td:
        tmpdir = Path(td)
        test_T2(tmpdir)
        test_T3(tmpdir)
        test_T4(tmpdir)
        test_T5(tmpdir)
        test_T6(tmpdir)
        test_T7(tmpdir)
    test_T8()
    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
