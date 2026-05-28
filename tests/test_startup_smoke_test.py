#!/usr/bin/env python3
"""OnePal Startup Smoke Test - Task 04-A (T1-T10)

Tests for the Runtime / Health / Startup Smoke Test baseline.

Usage:
    py tests/test_startup_smoke_test.py
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = "py"
PS = "powershell"

passed = 0
failed = 0


def run_cmd(cmd, timeout=180):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or "")[-3000:], (result.stderr or "")[-1000:]


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


# T1: runtime_service_registry.json parseable
def test_T1():
    print("\n--- T1: runtime_service_registry.json parseable ---")
    p = PROJECT_ROOT / "registries" / "runtime_service_registry.json"
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        ok = "services" in data and len(data.get("services", [])) >= 4
        return test("T1: registry parseable with >=4 services", ok)
    except Exception as e:
        return test("T1: registry parseable", False, str(e))


# T2: startup smoke test runs
def test_T2():
    print("\n--- T2: startup smoke test runs ---")
    ec, stdout, stderr = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "run_startup_smoke_test.py"),
    ])
    ok = ec in (0, 1)  # 0=ready/limited_ready, 1=not_ready/safe_mode
    return test("T2: startup smoke test runs", ok, stderr)


# T3: schema validation called successfully
def test_T3():
    print("\n--- T3: schema validation passes ---")
    ec, stdout, stderr = run_cmd([
        PS, "-ExecutionPolicy", "Bypass", "-File",
        str(PROJECT_ROOT / "scripts" / "validate_schema_registry.ps1"),
    ])
    return test("T3: schema validation", ec == 0, stderr[:200])


# T4: governance smoke test called
def test_T4():
    print("\n--- T4: governance smoke test passes ---")
    ec, stdout, stderr = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "run_governance_smoke_test.py"),
    ])
    return test("T4: governance smoke test", ec == 0, stderr[:200])


# T5: runtime smoke_tests JSONL writable and parseable
def test_T5():
    print("\n--- T5: runtime smoke_tests JSONL writable ---")
    test_file = PROJECT_ROOT / "runtime" / "smoke_tests" / "t5_test.jsonl"
    try:
        test_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {"test": "T5", "timestamp": "2026-05-22T00:00:00Z"}
        with open(test_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        with open(test_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    json.loads(line)
        return test("T5: smoke_tests JSONL writable+parseable", True)
    except Exception as e:
        return test("T5: smoke_tests JSONL writable", False, str(e))


# T6: runtime JSONL gitignored
def test_T6():
    print("\n--- T6: runtime JSONL gitignored ---")
    ec, stdout, stderr = run_cmd(
        ["git", "check-ignore", "-v", str(PROJECT_ROOT / "runtime" / "smoke_tests" / "t5_test.jsonl")],
        timeout=10,
    )
    return test("T6: smoke_tests JSONL gitignored", ec == 0, stdout.strip())


# T7: health_status.json generated but not git tracked
def test_T7():
    print("\n--- T7: health_status.json not git tracked ---")
    health = PROJECT_ROOT / "runtime" / "health_status.json"
    ok_file = health.exists()
    ec, stdout, stderr = run_cmd(["git", "check-ignore", "-v", str(health)], timeout=10)
    ok_ignored = ec == 0
    return test("T7: health_status.json exists and gitignored",
                ok_file and ok_ignored,
                f"exists={ok_file} ignored={ok_ignored}")


# T8: no secrets hit in project files
def test_T8():
    print("\n--- T8: no secrets hit ---")
    ec, stdout, stderr = run_cmd([
        "rg", "--no-heading", "-n", "-i",
        "(?:api[_-]?key|sk-[a-zA-Z0-9]{10,}|-----BEGIN.*KEY|token.*[=\\s][a-zA-Z0-9+/=]{20,})",
        "--glob", "!**/.git/**",
        "--glob", "!**/runtime/**",
        "--glob", "!**/logs/**",
        "--glob", "!**/node_modules/**",
        "--glob", "!**/.omo/**",
        "--glob", "!**/docs/**",
        "--glob", "!**/*.md",
        "--glob", "!scripts/run_startup_smoke_test.py",
        "--glob", "!tests/test_startup_smoke_test.py",
        "--glob", "!scripts/request_action.py",
        "--glob", "!scripts/memory_candidate.py",
        "--glob", "!scripts/research_packet.py",
        "--glob", "!tests/test_memory_center.py",
        "--glob", "!tests/test_api_server.py",
        "--glob", "!tests/test_research_center.py",
        "--glob", "!scripts/api_server.py",
        "--glob", "!registries/**",
        ".",
    ], timeout=30)
    hits = len(stdout.strip().split("\n")) if stdout.strip() else 0
    return test("T8: no secrets", hits == 0, f"{hits} hits" if hits else "clean")


# T9: check_runtime_lock.py runs
def test_T9():
    print("\n--- T9: check_runtime_lock.py runs ---")
    ec, stdout, stderr = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "check_runtime_lock.py"),
    ])
    ok = ec == 0
    try:
        json.loads(stdout.strip())
        ok = ok and True
    except:
        ok = False
    return test("T9: check_runtime_lock runs", ok, stdout.strip()[:150])


# T10: check_write_mode.py runs
def test_T10():
    print("\n--- T10: check_write_mode.py runs ---")
    ec, stdout, stderr = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "check_write_mode.py"),
    ])
    ok = ec == 0
    try:
        json.loads(stdout.strip())
        ok = ok and True
    except:
        ok = False
    return test("T10: check_write_mode runs", ok, stdout.strip()[:150])


def main():
    global passed, failed
    print("=" * 60)
    print("OnePal Startup Smoke Tests (T1-T10)")
    print("=" * 60)

    test_T1()
    test_T2()
    test_T3()
    test_T4()
    test_T5()
    test_T6()
    test_T7()
    test_T8()
    test_T9()
    test_T10()

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
