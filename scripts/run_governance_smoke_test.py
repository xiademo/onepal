#!/usr/bin/env python3
"""OnePal Governance Smoke Test Runner - Task 03-B

Runs:
  1. tests/test_governance_loop.py (T1-T12 governance tests)
  2. powershell -File scripts/validate_schema_registry.ps1
  3. JSONL parseability audit
  4. git check-ignore verification

Generates: docs/reports/task03b_governance_smoke_test_report.md

Usage:
    py scripts/run_governance_smoke_test.py
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "docs" / "reports" / "task03b_governance_smoke_test_report.md"

PY = "py"
PS = "powershell"


def run_cmd(cmd, timeout=120):
    """Run a command and return (exit_code, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout, result.stderr


def write_report(path, content):
    """Write generated Markdown with stable LF newlines and no trailing spaces."""
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n")).rstrip() + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(normalized)


def main():
    print("=" * 60)
    print("OnePal Governance Smoke Test Runner")
    print("=" * 60)

    results = {
        "governance_tests": {"status": "unknown", "output": ""},
        "schema_validation": {"status": "unknown", "output": ""},
        "jsonl_parse": {"status": "unknown", "output": ""},
        "git_ignore_check": {"status": "unknown", "output": ""},
    }

    # Phase 1: Governance Loop Tests (T1-T12)
    print("\n--- Phase 1: Governance Loop Tests ---")
    ec, stdout, stderr = run_cmd([PY, str(PROJECT_ROOT / "tests" / "test_governance_loop.py")])
    results["governance_tests"]["output"] = stdout + stderr
    results["governance_tests"]["status"] = "PASS" if ec == 0 else "FAIL"
    print(stdout[-500:] if len(stdout) > 500 else stdout)

    # Phase 2: Schema Validation
    print("\n--- Phase 2: Schema Validation ---")
    ec, stdout, stderr = run_cmd([
        PS, "-ExecutionPolicy", "Bypass", "-File",
        str(PROJECT_ROOT / "scripts" / "validate_schema_registry.ps1"),
    ])
    results["schema_validation"]["output"] = stdout + stderr
    results["schema_validation"]["status"] = "PASS" if ec == 0 else "FAIL"
    print(stdout[-500:] if len(stdout) > 500 else stdout)

    # Phase 3: JSONL Parse audit
    print("\n--- Phase 3: JSONL Parse Audit ---")
    runtime_dir = PROJECT_ROOT / "runtime"
    total_lines = 0
    bad_lines = 0
    for jsonl_path in runtime_dir.rglob("*.jsonl"):
        if jsonl_path.exists():
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    total_lines += 1
                    try:
                        json.loads(line)
                    except json.JSONDecodeError:
                        bad_lines += 1
    results["jsonl_parse"]["output"] = f"Total JSONL lines: {total_lines}, bad: {bad_lines}"
    results["jsonl_parse"]["status"] = "PASS" if bad_lines == 0 else "FAIL"
    print(f"  JSONL lines: {total_lines}, bad: {bad_lines}")

    # Phase 4: Git check-ignore
    print("\n--- Phase 4: Git check-ignore ---")
    paths_to_check = [
        "runtime/actions/action_executions.jsonl",
        "runtime/audit/state_mutation_audit.jsonl",
        "runtime/approvals/proposals.jsonl",
        "runtime/approvals/approval_decisions.jsonl",
    ]
    ignore_ok = True
    ignore_output = []
    for p in paths_to_check:
        ec, stdout, stderr = run_cmd(["git", "check-ignore", "-v", p])
        if ec == 0:
            ignore_output.append(f"  [IGNORED] {p} -> {stdout.strip()}")
        else:
            ignore_output.append(f"  [NOT IGNORED] {p}")
            ignore_ok = False
    results["git_ignore_check"]["output"] = "\n".join(ignore_output)
    results["git_ignore_check"]["status"] = "PASS" if ignore_ok else "FAIL"
    print("\n".join(ignore_output))

    # Generate report
    print("\n--- Generating Report ---")
    fails = sum(1 for r in results.values() if r["status"] == "FAIL")
    overall = "PASS" if fails == 0 else "FAIL"

    report = f"""# Task 03-B Governance Smoke Test Report

Generated: {datetime.now(timezone.utc).isoformat()}

## 1. Summary

| Phase | Status |
|-------|--------|
| Governance Tests (T1-T12) | {results['governance_tests']['status']} |
| Schema Validation | {results['schema_validation']['status']} |
| JSONL Parse Audit | {results['jsonl_parse']['status']} |
| Git Check-Ignore | {results['git_ignore_check']['status']} |
| **Overall** | **{overall}** |

## 2. Governance Tests (T1-T12)

```
{results['governance_tests']['output'][-2000:]}
```

## 3. Schema Validation

```
{results['schema_validation']['output'][-1000:]}
```

## 4. JSONL Parse Audit

{results['jsonl_parse']['output']}

## 5. Git Check-Ignore

```
{results['git_ignore_check']['output']}
```

## 6. Warnings

None.

## 7. Failures

{fails}

## 8. Next Step Recommendation

"""
    if overall == "PASS":
        report += "All governance smoke tests passed. Ready for Task 04.\n"
    else:
        report += f"**{fails} failures detected.** Resolve before proceeding.\n"

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_report(REPORT_PATH, report)
    print(f"Report written to: {REPORT_PATH}")

    print("\n" + "=" * 60)
    print(f"Overall: {overall}")
    print("=" * 60)

    sys.exit(0 if overall == "PASS" else 1)


if __name__ == "__main__":
    main()
