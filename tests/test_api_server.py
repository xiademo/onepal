#!/usr/bin/env python3
"""OnePal API Server Tests - Task 06 (T1-T17)

Usage: py tests/test_api_server.py
"""

import json
import os
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

# Add project root for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.api_server import (
    read_jsonl, build_response, handle_health, handle_tasks,
    handle_task_trees, handle_task_runs, handle_mas_trace, handle_command,
    HEALTH_PATH, TASKS_PATH, TREES_PATH, TASK_RUNS_PATH, MAS_TRACE_PATH,
    COMMAND_GATEWAY, MAX_LIMIT,
)

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


# --- Unit Tests: Core Functions ---

def test_T1():
    """T1: API server module importable."""
    print("\n--- T1: module importable ---")
    return test("T1: module importable", True)


def test_T2(tmpdir):
    """T2: 0.0.0.0 rejection."""
    print("\n--- T2: 0.0.0.0 rejection ---")
    from scripts.api_server import ALLOWED_HOSTS
    ok = "0.0.0.0" not in ALLOWED_HOSTS
    return test("T2: 0.0.0.0 not in ALLOWED_HOSTS", ok)


def test_T3(tmpdir):
    """T3: read_jsonl with missing file returns empty."""
    print("\n--- T3: read_jsonl missing file -> empty ---")
    results, skipped = read_jsonl(tmpdir / "nonexistent.jsonl", 10)
    return test("T3: missing file returns empty", results == [] and skipped == 0)


def test_T4(tmpdir):
    """T4: read_jsonl with valid JSONL."""
    print("\n--- T4: read_jsonl with valid JSONL ---")
    path = tmpdir / "test.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for i in range(5):
            f.write(json.dumps({"id": i}) + "\n")
    results, skipped = read_jsonl(path, 5)
    ok = len(results) == 5 and skipped == 0
    return test("T4: read_jsonl 5 valid lines", ok, f"lines={len(results)} skipped={skipped}")


def test_T5(tmpdir):
    """T5: read_jsonl with malformed lines skips them."""
    print("\n--- T5: read_jsonl skips malformed lines ---")
    path = tmpdir / "bad.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ok": 1}) + "\n")
        f.write("this is not json\n")
        f.write(json.dumps({"ok": 2}) + "\n")
    results, skipped = read_jsonl(path, 10)
    ok = len(results) == 2 and skipped == 1
    return test("T5: malformed lines skipped gracefully", ok, f"results={len(results)} skipped={skipped}")


def test_T6(tmpdir):
    """T6: read_jsonl limit clamped to MAX_LIMIT."""
    print("\n--- T6: read_jsonl limit clamped ---")
    path = tmpdir / "many.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for i in range(200):
            f.write(json.dumps({"id": i}) + "\n")
    results, _ = read_jsonl(path, 999)
    ok = len(results) == MAX_LIMIT
    return test("T6: limit clamped to 100", ok, f"got {len(results)}")


def test_T7(tmpdir):
    """T7: GET /health with health_status.json present."""
    print("\n--- T7: GET /health with file present ---")
    hpath = tmpdir / "health.json"
    hpath.write_text(json.dumps({"status": "ready", "checked_at": "2026-01-01T00:00:00Z"}), encoding="utf-8")
    resp = handle_health(hpath)
    ok = resp["ok"] and resp["data"].get("status") == "ready"
    return test("T7: health returns ok with ready status", ok, str(resp["data"].get("status")))


def test_T8(tmpdir):
    """T8: GET /health with file missing."""
    print("\n--- T8: GET /health with file missing ---")
    resp = handle_health(tmpdir / "nonexistent.json")
    ok = resp["ok"] and not resp["data"].get("exists")
    return test("T8: missing health returns ok with limited", ok, str(resp["data"].get("status")))


def test_T9(tmpdir):
    """T9: GET /tasks with file present."""
    print("\n--- T9: GET /tasks with file present ---")
    path = tmpdir / "tasks.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for i in range(3):
            f.write(json.dumps({"task_id": f"task_{i}"}) + "\n")
    resp = handle_tasks(path, 20)
    ok = resp["ok"] and len(resp["data"]["tasks"]) == 3
    return test("T9: tasks returns 3 items", ok, f"got {len(resp['data']['tasks'])}")


def test_T10(tmpdir):
    """T10: GET /task-trees with file present."""
    print("\n--- T10: GET /task-trees with file present ---")
    path = tmpdir / "trees.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"task_tree_id": "tree_1"}) + "\n")
    resp = handle_task_trees(path, 20)
    ok = resp["ok"] and len(resp["data"]["task_trees"]) == 1
    return test("T10: task-trees returns 1 item", ok, f"got {len(resp['data']['task_trees'])}")


def test_T11(tmpdir):
    """T11: GET /task-runs with file present."""
    print("\n--- T11: GET /task-runs with file present ---")
    path = tmpdir / "runs.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"task_run_id": "tr_1"}) + "\n")
    resp = handle_task_runs(path, 20)
    ok = resp["ok"] and len(resp["data"]["task_runs"]) == 1
    return test("T11: task-runs returns 1 item", ok)


def test_T12(tmpdir):
    """T12: GET /mas-trace with file present."""
    print("\n--- T12: GET /mas-trace with file present ---")
    path = tmpdir / "mas.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"event": "test"}) + "\n")
    resp = handle_mas_trace(path, 20)
    ok = resp["ok"] and len(resp["data"]["mas_trace"]) == 1
    return test("T12: mas-trace returns 1 item", ok)


def test_T13(tmpdir):
    """T13: POST /command rejects empty command."""
    print("\n--- T13: POST /command rejects empty command ---")
    gateway = Path(__file__).resolve().parent.parent / "scripts" / "command_gateway.py"
    resp = handle_command("", gateway)
    ok = not resp["ok"] and resp["error"]["code"] == "EMPTY_COMMAND"
    return test("T13: empty command rejected", ok, str(resp["error"]["code"]))


def test_T14(tmpdir):
    """T14: POST /command delegates to command_gateway.py."""
    print("\n--- T14: POST /command delegates to gateway ---")
    gateway = Path(__file__).resolve().parent.parent / "scripts" / "command_gateway.py"
    resp = handle_command("check health", gateway)
    ok = resp["ok"] and "gateway_result" in resp["data"]
    return test("T14: command delegates to gateway", ok, f"exit={resp['data'].get('gateway_exit_code')}")


def test_T15(tmpdir):
    """T15: POST /command rejects command exceeding max length."""
    print("\n--- T15: POST /command rejects overlong command ---")
    gateway = Path(__file__).resolve().parent.parent / "scripts" / "command_gateway.py"
    long_cmd = "x" * 3000
    resp = handle_command(long_cmd, gateway)
    ok = not resp["ok"] and resp["error"]["code"] == "COMMAND_TOO_LONG"
    return test("T15: overlong command rejected", ok)


def test_T16(tmpdir):
    """T16: build_response produces correct JSON structure."""
    print("\n--- T16: build_response structure ---")
    resp = build_response(True, data={"key": "val"})
    ok = all(k in resp for k in ("ok", "data", "error", "meta"))
    return test("T16: response has ok/data/error/meta", ok)


# --- Integration Test: Real HTTP Server ---

def test_T17():
    """T17: Real HTTP server starts, handles /health, stops."""
    print("\n--- T17: Real HTTP server integration ---")
    from scripts.api_server import create_server, OnePalHandler
    import tempfile
    from pathlib import Path

    tmpdir = Path(tempfile.mkdtemp(prefix="onepal_api_test_"))
    hpath = tmpdir / "health.json"
    hpath.write_text(json.dumps({"status": "ready", "checked_at": "2026-01-01T00:00:00Z"}), encoding="utf-8")

    # Configure handler
    class TestHandler(OnePalHandler):
        health_path = hpath

    server = create_server("127.0.0.1", 0, TestHandler)
    host = server.server_address[0]
    port = server.server_port

    try:
        # Start in thread
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.3)

        # Make request
        url = f"http://{host}:{port}/health"
        resp = urllib.request.urlopen(url, timeout=5)
        body = json.loads(resp.read().decode("utf-8"))
        ok = body.get("ok") and body["data"].get("status") == "ready"
        result = test("T17: real HTTP server /health returns ready", ok, str(body.get("data", {}).get("status")))
        return result
    except Exception as e:
        return test("T17: real HTTP server integration", False, str(e))
    finally:
        server.shutdown()
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    global passed, failed

    print("=" * 60)
    print("OnePal API Server Tests (T1-T17)")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="onepal_api_test_") as td:
        tmpdir = Path(td)
        test_T1()
        test_T2(tmpdir)
        test_T3(tmpdir)
        test_T4(tmpdir)
        test_T5(tmpdir)
        test_T6(tmpdir)
        test_T7(tmpdir)
        test_T8(tmpdir)
        test_T9(tmpdir)
        test_T10(tmpdir)
        test_T11(tmpdir)
        test_T12(tmpdir)
        test_T13(tmpdir)
        test_T14(tmpdir)
        test_T15(tmpdir)
        test_T16(tmpdir)

    test_T17()

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
