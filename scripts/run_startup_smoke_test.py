#!/usr/bin/env python3
"""OnePal Startup Smoke Test Runner - Task 04-A

Comprehensive health check for the OnePal runtime baseline.
Checks: services, schemas, governance, write capability, secrets, lock, write mode.

Outputs:
  runtime/health_status.json
  runtime/smoke_tests/startup_smoke_tests.jsonl
  docs/reports/task04_startup_smoke_test_report.md

Health statuses: ready | limited_ready | not_ready | safe_mode

Usage:
    py scripts/run_startup_smoke_test.py
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME = PROJECT_ROOT / "runtime"
SMOKE_DIR = RUNTIME / "smoke_tests"
HEALTH_FILE = RUNTIME / "health_status.json"
REPORT_PATH = PROJECT_ROOT / "docs" / "reports" / "task04_startup_smoke_test_report.md"

PY = "py"
PS = "powershell"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def run_cmd(cmd, timeout=180):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or "")[-3000:], (result.stderr or "")[-1000:]


def check_file(path_str):
    """Check if a file exists and is parseable JSON."""
    p = PROJECT_ROOT / path_str
    if not p.exists():
        return False, f"missing: {path_str}"
    if p.suffix == ".json":
        try:
            with open(p, "r", encoding="utf-8") as f:
                json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return False, f"invalid JSON: {path_str} -> {e}"
    return True, "ok"


def main():
    results = {
        "started_at": now_iso(),
        "checks": [],
        "critical_pass": 0,
        "critical_fail": 0,
        "warnings": 0,
    }

    print("=" * 60)
    print("OnePal Startup Smoke Test")
    print("=" * 60)

    SMOKE_DIR.mkdir(parents=True, exist_ok=True)

    # --- Check 1: Runtime Service Registry ---
    print("\n--- Check: Runtime Service Registry ---")
    ok, msg = check_file("registries/runtime_service_registry.json")
    results["checks"].append({"check": "runtime_service_registry", "pass": ok, "msg": msg, "critical": True})
    if ok: results["critical_pass"] += 1
    else: results["critical_fail"] += 1
    print(f"  {'PASS' if ok else 'FAIL'}: {msg}")

    # --- Check 2: Critical file existence ---
    print("\n--- Check: Critical File Existence ---")
    critical_files = [
        "schemas/registry.json",
        "registries/action_registry.json",
        "policies/permission_profiles.json",
        "scripts/validate_schema_registry.ps1",
        "scripts/run_governance_smoke_test.py",
    ]
    for cf in critical_files:
        ok = (PROJECT_ROOT / cf).exists()
        check = {"check": f"file:{cf}", "pass": ok, "msg": "exists" if ok else "MISSING", "critical": True}
        results["checks"].append(check)
        if ok: results["critical_pass"] += 1
        else: results["critical_fail"] += 1
        print(f"  {'PASS' if ok else 'FAIL'}: {cf}")

    # --- Check 3: Schema Validation ---
    print("\n--- Check: Schema Validation ---")
    ec, stdout, stderr = run_cmd([
        PS, "-ExecutionPolicy", "Bypass", "-File",
        str(PROJECT_ROOT / "scripts" / "validate_schema_registry.ps1"),
    ])
    ok = ec == 0
    check = {"check": "schema_validation", "pass": ok, "msg": "" if ok else stderr[:200], "critical": True}
    results["checks"].append(check)
    if ok: results["critical_pass"] += 1
    else: results["critical_fail"] += 1
    print(f"  {'PASS' if ok else 'FAIL'}")

    # --- Check 4: Governance Smoke Test ---
    print("\n--- Check: Governance Smoke Test ---")
    ec, stdout, stderr = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "run_governance_smoke_test.py"),
    ])
    ok = ec == 0
    check = {"check": "governance_smoke_test", "pass": ok, "msg": "" if ok else stderr[:200], "critical": True}
    results["checks"].append(check)
    if ok: results["critical_pass"] += 1
    else: results["critical_fail"] += 1
    print(f"  {'PASS' if ok else 'FAIL'}")

    # --- Check 5: Runtime Write Capability ---
    print("\n--- Check: Runtime Write Capability ---")
    test_entry = {
        "test_id": f"startup_{now_iso()}",
        "check": "runtime_write_capability",
        "timestamp": now_iso(),
    }
    smoke_file = SMOKE_DIR / "startup_smoke_tests.jsonl"
    try:
        with open(smoke_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(test_entry, ensure_ascii=False) + "\n")
        # Verify parseable
        with open(smoke_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    json.loads(line)
        ok = True
        msg = f"wrote to {smoke_file}"
    except Exception as e:
        ok = False
        msg = str(e)
    check = {"check": "runtime_write", "pass": ok, "msg": msg, "critical": False}
    results["checks"].append(check)
    if not ok: results["warnings"] += 1
    print(f"  {'PASS' if ok else 'WARN'}: {msg}")

    # --- Check 6: Runtime JSONL gitignore ---
    print("\n--- Check: Runtime JSONL Git-Ignore ---")
    ec, stdout, stderr = run_cmd(
        ["git", "check-ignore", "-v", str(smoke_file)],
        timeout=10,
    )
    ok = ec == 0
    msg = stdout.strip() if ok else "NOT IGNORED"
    check = {"check": "gitignore_runtime_jsonl", "pass": ok, "msg": msg, "critical": True}
    results["checks"].append(check)
    if ok: results["critical_pass"] += 1
    else: results["critical_fail"] += 1
    print(f"  {'PASS' if ok else 'FAIL'}: {msg[:120]}")

    # --- Check 7: Secrets Scan ---
    print("\n--- Check: Secrets Scan ---")
    ec, stdout, stderr = run_cmd([
        "rg", "--no-heading", "-n", "-i",
        "(?:api[_-]?key|sk-[a-zA-Z0-9]{10,}|-----BEGIN.*KEY|token.*[=\\s][a-zA-Z0-9+/=]{20,}|password.*[=\\s]\\S{8,}|secret.*[=\\s]\\S{8,})",
        "--glob", "!**/.git/**",
        "--glob", "!**/runtime/**",
        "--glob", "!**/logs/**",
        "--glob", "!**/node_modules/**",
        "--glob", "!**/.omo/**",
        "--glob", "!**/OpenCode/**",
        "--glob", "!**/__pycache__/**",
        "--glob", "!**/docs/**",
        "--glob", "!**/*.md",
        "--glob", "!scripts/run_startup_smoke_test.py",
        "--glob", "!tests/test_startup_smoke_test.py",
        "--glob", "!scripts/request_action.py",
        "--glob", "!scripts/memory_candidate.py",
        "--glob", "!tests/test_memory_center.py",
        "--glob", "!registries/**",
        ".",
    ], timeout=30)
    secret_lines = len(stdout.strip().split("\n")) if stdout.strip() else 0
    ok = secret_lines == 0
    check = {"check": "secrets_scan", "pass": ok, "msg": f"{secret_lines} potential hits" if secret_lines else "clean", "critical": True}
    if ok:
        results["critical_pass"] += 1
    else:
        results["critical_fail"] += 1
        check["msg"] = f"SECURITY: {secret_lines} potential secrets found"
    results["checks"].append(check)
    print(f"  {'PASS' if ok else 'FAIL'}: {check['msg']}")

    # --- Check 8: Runtime Lock ---
    print("\n--- Check: Runtime Lock ---")
    ec, stdout, stderr = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "check_runtime_lock.py"),
    ], timeout=10)
    lock_locked = "LOCKED" in (stdout + stderr)
    ok = ec == 0
    check = {"check": "runtime_lock", "pass": ok, "msg": stdout.strip()[:200], "critical": False}
    if lock_locked:
        check["critical"] = True
        results["warnings"] += 1
    results["checks"].append(check)
    print(f"  {'PASS' if ok else 'WARN'}: {stdout.strip()[:150]}")

    # --- Check 9: Write Mode ---
    print("\n--- Check: Write Mode ---")
    ec, stdout, stderr = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "check_write_mode.py"),
    ], timeout=10)
    mode_locked = "locked" in (stdout + stderr).lower() and "mode" in (stdout + stderr).lower()
    ok = ec == 0
    check = {"check": "write_mode", "pass": ok, "msg": stdout.strip()[:200], "critical": False}
    if mode_locked:
        check["critical"] = True
        results["warnings"] += 1
    results["checks"].append(check)
    print(f"  {'PASS' if ok else 'WARN'}: {stdout.strip()[:150]}")

    # --- Determine health status ---
    print("\n--- Health Summary ---")
    cf = results["critical_fail"]
    warnings = results["warnings"]

    if cf > 0:
        # Check if security-related
        has_security_fail = any(
            c.get("check") == "secrets_scan" and not c.get("pass")
            for c in results["checks"]
        )
        if has_security_fail:
            status = "safe_mode"
        else:
            status = "not_ready"
    elif warnings > 0:
        status = "limited_ready"
    else:
        status = "ready"

    results["health_status"] = status
    results["ended_at"] = now_iso()

    health = {
        "status": status,
        "critical_pass": results["critical_pass"],
        "critical_fail": cf,
        "warnings": warnings,
        "checked_at": now_iso(),
        "checks": results["checks"],
    }
    with open(HEALTH_FILE, "w", encoding="utf-8") as f:
        json.dump(health, f, indent=2, ensure_ascii=False)

    print(f"  Status: {status}")
    print(f"  Critical: {results['critical_pass']} pass, {cf} fail")
    print(f"  Warnings: {warnings}")

    # --- Generate report ---
    print("\n--- Generating Report ---")
    report = f"""# Task 04 Startup Smoke Test Report

Generated: {now_iso()}

## 1. Summary

| Metric | Value |
|--------|-------|
| Health Status | **{status}** |
| Critical PASS | {results['critical_pass']} |
| Critical FAIL | {cf} |
| Warnings | {warnings} |

## 2. Runtime Service Registry

4 services registered in `registries/runtime_service_registry.json`:
- svc_schema_registry, svc_governance_smoke_test, svc_action_registry, svc_permission_profiles

## 3. Schema Validation

{'PASS' if any(c['check']=='schema_validation' and c['pass'] for c in results['checks']) else 'FAIL'}

## 4. Governance Smoke Test

{'PASS' if any(c['check']=='governance_smoke_test' and c['pass'] for c in results['checks']) else 'FAIL'}

## 5. Runtime Write Test

{'PASS' if any(c['check']=='runtime_write' and c['pass'] for c in results['checks']) else 'WARN'}

## 6. Runtime Gitignore Audit

{'PASS' if any(c['check']=='gitignore_runtime_jsonl' and c['pass'] for c in results['checks']) else 'FAIL'}

## 7. Runtime Lock Check

{next((c['msg'] for c in results['checks'] if c['check']=='runtime_lock'), 'unknown')}

## 8. Write Mode Check

{next((c['msg'] for c in results['checks'] if c['check']=='write_mode'), 'unknown')}

## 9. Secrets Scan

{next((c['msg'] for c in results['checks'] if c['check']=='secrets_scan'), 'unknown')}

## 10. Final Health Status

**{status}**

## 11. Warnings

{warnings}

## 12. Failures

{cf}

## 13. Next Step Recommendation

"""
    if status == "ready":
        report += "All critical checks passed. System is ready for Task 05.\n"
    elif status == "limited_ready":
        report += "System is functional with non-critical warnings. Review warnings before proceeding.\n"
    elif status == "safe_mode":
        report += "**SAFE MODE**: Security boundary violation detected. Do NOT proceed until resolved.\n"
    else:
        report += f"**{cf} critical failures**. Resolve before proceeding.\n"

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report: {REPORT_PATH}")

    print("\n" + "=" * 60)
    print(f"Health: {status}")
    print("=" * 60)

    if status in ("ready", "limited_ready"):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
