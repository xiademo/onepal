#!/usr/bin/env python3
"""OnePal local assistant usability tests.

Usage: py tests/test_local_assistant_usage.py
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

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
            print(f"         {msg}")
    return ok


def read(path):
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def test_scripts_exist_and_target_local_api():
    print("\n--- U1: launcher scripts ---")
    start = PROJECT_ROOT / "scripts" / "start_onepal.ps1"
    stop = PROJECT_ROOT / "scripts" / "stop_onepal.ps1"
    ok = start.exists() and stop.exists()
    test("U1a: start/stop scripts exist", ok)

    content = start.read_text(encoding="utf-8")
    expected = [
        "127.0.0.1",
        "18790",
        "scripts\\api_server.py",
        "dashboard\\index.html",
        "Start-Process",
        "-WindowStyle Hidden",
    ]
    test("U1b: start script targets local API and dashboard", all(item in content for item in expected))

    stop_content = stop.read_text(encoding="utf-8")
    test("U1c: stop script uses PID file", "onepal_api.pid" in stop_content and "Stop-Process" in stop_content)


def test_runtime_artifacts_ignored():
    print("\n--- U2: runtime artifacts ignored ---")
    gitignore = read(".gitignore")
    ok = "runtime/*.pid" in gitignore and "runtime/*.log" in gitignore
    test("U2: launcher PID/log files are gitignored", ok)


def test_manual_and_readme():
    print("\n--- U3: manual and README ---")
    manual_path = PROJECT_ROOT / "docs" / "user_manual.md"
    test("U3a: user manual exists", manual_path.exists())

    manual = manual_path.read_text(encoding="utf-8")
    required_manual_terms = [
        "scripts/start_onepal.ps1",
        "scripts/stop_onepal.ps1",
        "http://127.0.0.1:18790",
        "Dashboard",
        "Memory",
        "Research",
        "Growth",
        "Career",
        "MCP、LiteLLM、RAG、n8n 当前没有启用",
    ]
    test("U3b: manual covers startup, panels, and safety", all(term in manual for term in required_manual_terms))

    readme = read("README.md")
    ok = "scripts/start_onepal.ps1" in readme and "docs/user_manual.md" in readme
    test("U3c: README points to quick start and manual", ok)


def main():
    print("=" * 60)
    print("OnePal Local Assistant Usage Tests")
    print("=" * 60)
    test_scripts_exist_and_target_local_api()
    test_runtime_artifacts_ignored()
    test_manual_and_readme()

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{passed + failed} PASS, {failed}/{passed + failed} FAIL")
    print("=" * 60)
    raise SystemExit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
