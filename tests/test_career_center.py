#!/usr/bin/env python3
"""OnePal Career Center Tests - Task 15.

Usage: py tests/test_career_center.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
SCRIPT = PROJECT_ROOT / "scripts" / "career_center.py"

SCHEMAS = [
    "career_asset.schema.json",
    "resume_claim.schema.json",
    "jd_item.schema.json",
    "jd_evaluation.schema.json",
    "application_record.schema.json",
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
        "assets": tmpdir / "career" / "assets.jsonl",
        "claims": tmpdir / "career" / "claims.jsonl",
        "jds": tmpdir / "career" / "jds.jsonl",
        "evaluations": tmpdir / "career" / "evaluations.jsonl",
        "applications": tmpdir / "career" / "applications.jsonl",
        "handoffs": tmpdir / "career" / "handoffs.jsonl",
        "audit": tmpdir / "logs" / "career_audit.jsonl",
    }


def path_args(p):
    return [
        "--assets-log", str(p["assets"]),
        "--claims-log", str(p["claims"]),
        "--jds-log", str(p["jds"]),
        "--evaluations-log", str(p["evaluations"]),
        "--applications-log", str(p["applications"]),
        "--handoffs-log", str(p["handoffs"]),
        "--audit-log", str(p["audit"]),
    ]


def test_T1():
    print("\n--- T1: files and schemas exist ---")
    ok = SCRIPT.exists() and (PROJECT_ROOT / "career" / "README.md").exists()
    test("T1: Career script and README exist", ok)
    registry = json.loads((PROJECT_ROOT / "schemas" / "registry.json").read_text(encoding="utf-8"))
    ids = {entry["schema_id"] for entry in registry.get("schemas", [])}
    for sid in SCHEMAS:
        schema_path = PROJECT_ROOT / "schemas" / "core" / sid
        test(f"T1-{sid}: schema registered", schema_path.exists() and sid in ids)


def test_T2(tmpdir):
    print("\n--- T2: asset creation requires evidence status ---")
    p = paths(tmpdir / "t2")
    result = run_cmd([PY, str(SCRIPT), "asset-create", "--asset-type", "project",
                      "--title", "OnePal Growth API", "--summary", "Implemented Growth Center API"] + path_args(p))
    data = parse(result)
    asset = data.get("asset", {})
    ok = data.get("status") == "created" and asset.get("status") == "needs_evidence"
    return test("T2: asset without evidence marked needs_evidence", ok, str(data))


def test_T3(tmpdir):
    print("\n--- T3: evidence-backed claim ready ---")
    p = paths(tmpdir / "t3")
    asset_data = parse(run_cmd([PY, str(SCRIPT), "asset-create", "--asset-type", "project",
                                "--title", "Schema work", "--summary", "Added schema pack",
                                "--evidence-refs", "commit:abc123"] + path_args(p)))
    aid = asset_data["asset"]["asset_id"]
    claim_data = parse(run_cmd([PY, str(SCRIPT), "claim-create",
                                "--claim-text", "Implemented schema governance for OnePal",
                                "--asset-refs", aid] + path_args(p)))
    claim = claim_data.get("claim", {})
    ok = claim.get("status") == "ready" and claim.get("confidence", 0) >= 0.8 and aid in claim.get("asset_refs", [])
    return test("T3: claim backed by asset is ready", ok, str(claim))


def test_T4(tmpdir):
    print("\n--- T4: JD evaluation deterministic and missing evidence visible ---")
    p = paths(tmpdir / "t4")
    jd_data = parse(run_cmd([PY, str(SCRIPT), "jd-create", "--title", "AI Engineer",
                             "--company", "LocalCo", "--description-summary", "Build APIs",
                             "--requirements", "python api,governance"] + path_args(p)))
    jd_id = jd_data["jd"]["jd_id"]
    eval_data = parse(run_cmd([PY, str(SCRIPT), "jd-evaluate", "--jd-id", jd_id] + path_args(p)))
    ev = eval_data.get("evaluation", {})
    ok = ev.get("status") == "needs_evidence" and ev.get("recommendation") == "needs_evidence" and ev.get("missing_requirements")
    return test("T4: evaluation degrades when claims missing", ok, str(ev))


def test_T5(tmpdir):
    print("\n--- T5: JD evaluation matches ready claims ---")
    p = paths(tmpdir / "t5")
    asset_data = parse(run_cmd([PY, str(SCRIPT), "asset-create", "--asset-type", "project",
                                "--title", "API project", "--summary", "Python API governance",
                                "--evidence-refs", "test:test_api_server"] + path_args(p)))
    aid = asset_data["asset"]["asset_id"]
    parse(run_cmd([PY, str(SCRIPT), "claim-create", "--claim-text", "Built python api governance",
                   "--asset-refs", aid] + path_args(p)))
    jd_data = parse(run_cmd([PY, str(SCRIPT), "jd-create", "--title", "Backend Engineer",
                             "--requirements", "python api"] + path_args(p)))
    ev = parse(run_cmd([PY, str(SCRIPT), "jd-evaluate", "--jd-id", jd_data["jd"]["jd_id"]] + path_args(p))).get("evaluation", {})
    ok = ev.get("score", 0) >= 1 and ev.get("matched_claim_refs")
    return test("T5: evaluation matches claim", ok, str(ev))


def test_T6(tmpdir):
    print("\n--- T6: application record manual only ---")
    p = paths(tmpdir / "t6")
    jd_data = parse(run_cmd([PY, str(SCRIPT), "jd-create", "--title", "Manual Role"] + path_args(p)))
    app = parse(run_cmd([PY, str(SCRIPT), "application-create", "--jd-id", jd_data["jd"]["jd_id"],
                         "--notes", "prepare draft"] + path_args(p))).get("application", {})
    ok = app.get("status") == "manual_review" and app.get("auto_submit") is False
    return test("T6: application manual_review and auto_submit false", ok, str(app))


def test_T7(tmpdir):
    print("\n--- T7: career handoff captured ---")
    p = paths(tmpdir / "t7")
    data = parse(run_cmd([PY, str(SCRIPT), "handoff-create", "--source-type", "growth",
                          "--source-id", "goal_1", "--summary", "career goal handoff"] + path_args(p)))
    handoff = data.get("handoff", {})
    ok = data.get("status") == "created" and handoff.get("handoff_id", "").startswith("careerhandoff_")
    return test("T7: handoff captured", ok, str(data))


def test_T8(tmpdir):
    print("\n--- T8: secret-like content rejected ---")
    p = paths(tmpdir / "t8")
    result = run_cmd([PY, str(SCRIPT), "claim-create", "--claim-text", "token=abcdefghijklmnopqrstuvwxyz"] + path_args(p))
    ok = result.returncode != 0 and load_jsonl(p["claims"]) == []
    return test("T8: secret claim rejected", ok, f"exit={result.returncode}")


def test_T9():
    print("\n--- T9: static safety and gitignore ---")
    text = SCRIPT.read_text(encoding="utf-8")
    stripped = "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))
    no_shell_network = "shell=True" not in stripped and "http://" not in stripped and "https://" not in stripped
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    ignored = "career/**/*.jsonl" in gitignore and "logs/career_audit.jsonl" in gitignore
    test("T9: no shell/network in Career script", no_shell_network)
    test("T9b: Career runtime data gitignored", ignored)


def main():
    print("=" * 60)
    print("OnePal Career Center Tests")
    print("=" * 60)
    test_T1()
    with tempfile.TemporaryDirectory(prefix="onepal_career_test_") as td:
        tmpdir = Path(td)
        test_T2(tmpdir)
        test_T3(tmpdir)
        test_T4(tmpdir)
        test_T5(tmpdir)
        test_T6(tmpdir)
        test_T7(tmpdir)
        test_T8(tmpdir)
    test_T9()
    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
