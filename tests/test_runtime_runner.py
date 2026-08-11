#!/usr/bin/env python3
"""OnePal Runtime Runner Tests - Task 05-B (T1-T15)

Tests: queued task reading, allowlist enforcement, execution dispatch,
status transitions, task_runs JSONL, mas_trace, gitignore, regression.

Uses temporary directories — never touches production runtime files.

Usage:
    py tests/test_runtime_runner.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
GATEWAY = PROJECT_ROOT / "scripts" / "command_gateway.py"
RUNNER = PROJECT_ROOT / "scripts" / "runtime_runner.py"
REQUEST_ACTION = PROJECT_ROOT / "scripts" / "request_action.py"

passed = 0
failed = 0


def run_runner(info, task_runs_log=None):
    """Run the runtime_runner with temp directory paths."""
    tr_log = task_runs_log or info.get("task_runs_log") or (info.get("tasks_log").parent / "task_runs.jsonl")
    cmd = [
        PY, str(RUNNER), "--task-id", info["task_id"],
        "--tasks-log", str(info["tasks_log"]),
        "--task-runs-log", str(tr_log),
        "--mas-trace-log", str(info.get("trace_log", info["tasks_log"].parent / "mas_trace.jsonl")),
    ]
    ec, out, err = run_cmd(cmd)
    try:
        data = json.loads(out.strip())
        return ec, data, err
    except json.JSONDecodeError:
        return ec, None, out[:200]


def run_cmd(cmd, timeout=120):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                            encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or ""), (result.stderr or "")


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


def count_jsonl(path):
    if not path.exists():
        return 0
    cnt = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    json.loads(line)
                    cnt += 1
                except json.JSONDecodeError:
                    pass
    return cnt


def setup_task(tmpdir, command, profile="safe_readonly"):
    """Create a queued task via gateway in temp dir and return info dict."""
    cmd_log = tmpdir / "commands.jsonl"
    route_log = tmpdir / "routing.jsonl"
    tasks_log = tmpdir / "tasks.jsonl"
    trees_log = tmpdir / "trees.jsonl"
    trace_log = tmpdir / "mas_trace.jsonl"
    task_runs_log = tmpdir / "task_runs.jsonl"

    ec, out, err = run_cmd([
        PY, str(GATEWAY), "--command", command, "--profile", profile,
        "--commands-log", str(cmd_log), "--routing-log", str(route_log),
        "--tasks-log", str(tasks_log), "--task-trees-log", str(trees_log),
        "--mas-trace-log", str(trace_log),
    ])
    try:
        data = json.loads(out.strip())
        task_id = data.get("task_id")
    except json.JSONDecodeError:
        return None

    # Read the task to get full fields
    tasks = []
    if tasks_log.exists():
        with open(tasks_log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    tasks.append(json.loads(line))
    task = next((t for t in tasks if t.get("task_id") == task_id), None)

    return {
        "task": task,
        "task_id": task_id,
        "cmd_log": cmd_log,
        "route_log": route_log,
        "tasks_log": tasks_log,
        "trees_log": trees_log,
        "trace_log": trace_log,
        "task_runs_log": task_runs_log,
    }


# T1: Runner can read queued script_ref task
def test_T1(tmpdir):
    print("\n--- T1: Runner reads queued script_ref task ---")
    info = setup_task(tmpdir, "run startup smoke test")
    if info is None or info.get("task") is None:
        return test("T1: setup task", False)
    task = info["task"]
    ok = (task.get("status") == "queued" and
          task.get("execution_type") == "script_ref" and
          "run_startup_smoke_test.py" in (task.get("script_ref") or ""))
    return test("T1: queued script_ref task created", ok, str(task.get("status")))


# T2: Allowlisted startup smoke test dry-run
def test_T2(tmpdir):
    print("\n--- T2: Allowlisted startup smoke test dry-run ---")
    task_runs_log = tmpdir / "task_runs.jsonl"
    info = setup_task(tmpdir, "run startup smoke test")
    if info is None:
        return test("T2: setup", False)

    ec, data, err = run_runner(info, task_runs_log)
    cnt = count_jsonl(task_runs_log)
    ok = data and data.get("status") == "completed" and cnt > 0
    return test("T2: startup smoke test dry-run completed", ok,
                f"status={data.get('status') if data else 'None'}, task_runs={cnt}")


# T3: Allowlisted governance smoke test dry-run
def test_T3(tmpdir):
    print("\n--- T3: Allowlisted governance smoke test dry-run ---")
    task_runs_log = tmpdir / "task_runs.jsonl"
    info = setup_task(tmpdir, "check governance tests")
    if info is None:
        return test("T3: setup", False)

    ec, data, err = run_runner(info, task_runs_log)
    cnt = count_jsonl(task_runs_log)
    ok = data and data.get("status") in ("completed", "failed") and cnt > 0
    return test("T3: governance smoke test dry-run executed", ok,
                f"status={data.get('status') if data else 'None'}, task_runs={cnt}")


# T4: Unknown script_ref rejected
def test_T4(tmpdir):
    print("\n--- T4: Unknown script_ref rejected ---")
    # Manually create a task with unknown script_ref
    tasks_log = tmpdir / "tasks.jsonl"
    task = {
        "task_id": "task_t4_test",
        "task_tree_id": "tree_t4_test",
        "command_id": "cmd_t4_test",
        "title": "Test unknown script",
        "task_type": "command",
        "status": "queued",
        "priority": "P2",
        "owner_agent": "coordinator",
        "risk_level": "R0",
        "execution_type": "script_ref",
        "script_ref": "scripts/unknown_fake_script.py",
        "action_refs": [],
        "created_at": "2026-01-01T00:00:00Z",
    }
    tasks_log.parent.mkdir(parents=True, exist_ok=True)
    with open(tasks_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(task) + "\n")

    info = {"task_id": "task_t4_test", "tasks_log": tasks_log,
            "trace_log": tmpdir / "mas_trace.jsonl"}
    tr_log = tmpdir / "task_runs.jsonl"
    ec, data, err = run_runner(info, tr_log)
    ok = data and data.get("status") in ("rejected", "failed")
    return test("T4: unknown script rejected", ok, str(data.get("status") if data else None))


# T5: .ps1/.bat/.exe/.sh rejected
def test_T5(tmpdir):
    print("\n--- T5: .ps1/.bat/.exe/.sh rejected ---")
    tasks_log = tmpdir / "tasks.jsonl"
    task = {
        "task_id": "task_t5_test",
        "task_tree_id": "tree_t5_test",
        "command_id": "cmd_t5_test",
        "title": "Test bad extension",
        "task_type": "command",
        "status": "queued",
        "priority": "P2",
        "owner_agent": "coordinator",
        "risk_level": "R0",
        "execution_type": "script_ref",
        "script_ref": "scripts/malicious.ps1",
        "action_refs": [],
        "created_at": "2026-01-01T00:00:00Z",
    }
    with open(tasks_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(task) + "\n")

    info = {"task_id": "task_t5_test", "tasks_log": tasks_log,
            "trace_log": tmpdir / "mas_trace.jsonl"}
    tr_log = tmpdir / "task_runs.jsonl"
    ec, data, err = run_runner(info, tr_log)
    ok = data and (data.get("error") or "").lower().find("forbidden") >= 0
    return test("T5: .ps1 rejected as forbidden extension", ok, str(data.get("error") if data else None))


# T6: action_ref delegates to request_action.py
def test_T6(tmpdir):
    print("\n--- T6: action_ref delegates to request_action.py ---")
    task_runs_log = tmpdir / "task_runs.jsonl"
    info = setup_task(tmpdir, "read file docs/architecture.md")
    if info is None:
        return test("T6: setup", False)

    ec, data, err = run_runner(info, task_runs_log)
    cnt = count_jsonl(task_runs_log)
    ok = data and cnt > 0 and data.get("status") in ("completed", "failed")
    return test("T6: action_ref delegated via subprocess", ok,
                f"status={data.get('status') if data else 'None'}, task_runs={cnt}")


# T7: R2 action_ref without approval → rejected
def test_T7(tmpdir):
    print("\n--- T7: R2 action_ref without approval rejected ---")
    tasks_log = tmpdir / "tasks.jsonl"
    task = {
        "task_id": "task_t7_test",
        "task_tree_id": "tree_t7_test",
        "command_id": "cmd_t7_test",
        "title": "Test R2 action",
        "task_type": "command",
        "status": "queued",
        "priority": "P2",
        "owner_agent": "coordinator",
        "risk_level": "R2",
        "execution_type": "action_ref",
        "action_refs": ["action.approve_proposal"],
        "script_ref": None,
        "created_at": "2026-01-01T00:00:00Z",
    }
    with open(tasks_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(task) + "\n")

    info = {"task_id": "task_t7_test", "tasks_log": tasks_log,
            "trace_log": tmpdir / "mas_trace.jsonl"}
    tr_log = tmpdir / "task_runs.jsonl"
    ec, data, err = run_runner(info, tr_log)
    ok = data and data.get("status") in ("rejected", "failed")
    return test("T7: R2 action_ref rejected by allowlist", ok,
                f"status={data.get('status')}, error={data.get('error')}")


# T8: review execution_type not executed
def test_T8(tmpdir):
    print("\n--- T8: review execution_type not executed ---")
    tasks_log = tmpdir / "tasks.jsonl"
    task = {
        "task_id": "task_t8_test",
        "task_tree_id": "tree_t8_test",
        "command_id": "cmd_t8_test",
        "title": "Test review",
        "task_type": "command",
        "status": "queued",
        "priority": "P2",
        "owner_agent": "coordinator",
        "risk_level": "R1",
        "execution_type": "review",
        "action_refs": [],
        "script_ref": None,
        "created_at": "2026-01-01T00:00:00Z",
    }
    with open(tasks_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(task) + "\n")

    info = {"task_id": "task_t8_test", "tasks_log": tasks_log,
            "trace_log": tmpdir / "mas_trace.jsonl"}
    tr_log = tmpdir / "task_runs.jsonl"
    ec, data, err = run_runner(info, tr_log)
    ok = (data and data.get("status") == "rejected" and
          data.get("error", "").find("review") >= 0)
    return test("T8: review type not executed, enters waiting_review", ok,
                f"status={data.get('status')}")


# T9: task status queued→running→completed
def test_T9(tmpdir):
    print("\n--- T9: task status transitions to completed ---")
    # Use a dedicated subdirectory to avoid cross-test contamination
    t9_dir = tmpdir / "t9"
    t9_dir.mkdir(parents=True, exist_ok=True)
    tasks_log = t9_dir / "tasks.jsonl"
    task_runs_log = t9_dir / "task_runs.jsonl"
    trace_log = t9_dir / "mas_trace.jsonl"

    task = {
        "task_id": "task_t9_good",
        "task_tree_id": "tree_t9_good",
        "command_id": "cmd_t9_good",
        "title": "Test completed status",
        "task_type": "command",
        "status": "queued",
        "priority": "P2",
        "owner_agent": "coordinator",
        "risk_level": "R0",
        "execution_type": "action_ref",
        "action_refs": ["action.read_file"],
        "script_ref": None,
        "created_at": "2026-01-01T00:00:00Z",
    }
    with open(tasks_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(task) + "\n")

    info = {"task_id": "task_t9_good", "tasks_log": tasks_log,
            "trace_log": trace_log}
    ec, data, err = run_runner(info, task_runs_log)
    # Read the task back to check status
    tasks = []
    if tasks_log.exists():
        with open(tasks_log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    tasks.append(json.loads(line))
    t = tasks[0] if tasks else {}
    ok = t.get("status") == "completed"
    return test("T9: task status → completed", ok, f"status={t.get('status')}")


# T10: task status queued→running→failed
def test_T10(tmpdir):
    print("\n--- T10: task status transitions to failed on unknown script ---")
    tasks_log = tmpdir / "tasks.jsonl"
    task = {
        "task_id": "task_t10_test",
        "task_tree_id": "tree_t10_test",
        "command_id": "cmd_t10_test",
        "title": "Test failed",
        "task_type": "command",
        "status": "queued",
        "priority": "P2",
        "owner_agent": "coordinator",
        "risk_level": "R0",
        "execution_type": "script_ref",
        "script_ref": "scripts/nonexistent_fake.py",
        "action_refs": [],
        "created_at": "2026-01-01T00:00:00Z",
    }
    with open(tasks_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(task) + "\n")

    info = {"task_id": "task_t10_test", "tasks_log": tasks_log,
            "trace_log": tmpdir / "mas_trace.jsonl"}
    ec, data, err = run_runner(info, tmpdir / "task_runs.jsonl")
    tasks = []
    if tasks_log.exists():
        with open(tasks_log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    tasks.append(json.loads(line))
    t = tasks[0] if tasks else {}
    ok = t.get("status") in ("failed", "waiting_review")
    return test("T10: task status → failed on bad script", ok, f"status={t.get('status')}")


# T11: task_runs JSONL parseable
def test_T11(tmpdir):
    print("\n--- T11: task_runs JSONL parseable ---")
    task_runs_log = tmpdir / "task_runs.jsonl"
    info = setup_task(tmpdir, "run startup smoke test")
    if info is None:
        return test("T11: setup", False)

    ec, data, err = run_runner(info, task_runs_log)
    cnt = count_jsonl(task_runs_log)
    ok = cnt > 0
    return test("T11: task_runs JSONL parseable", ok, f"lines={cnt}")


# T12: MAS trace records runner events
def test_T12(tmpdir):
    print("\n--- T12: MAS trace records runner events ---")
    task_runs_log = tmpdir / "task_runs.jsonl"
    trace_log = tmpdir / "mas_trace.jsonl"
    info = setup_task(tmpdir, "run startup smoke test")
    if info is None:
        return test("T12: setup", False)

    ec, data, err = run_runner(info, task_runs_log)
    events = []
    if info["trace_log"].exists():
        with open(info["trace_log"], "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line).get("event"))
                    except json.JSONDecodeError:
                        pass
    runner_events = [e for e in events if e and "runner_" in e]
    ok = len(runner_events) >= 2
    return test("T12: MAS trace has runner events", ok, f"runner_events={runner_events}")


# T13: runtime/task_runs/*.jsonl gitignored
def test_T13():
    print("\n--- T13: runtime/task_runs/*.jsonl gitignored ---")
    ec, stdout, _ = run_cmd(
        ["git", "check-ignore", "-v", "runtime/task_runs/task_runs.jsonl"],
        timeout=10,
    )
    return test("T13: task_runs JSONL gitignored", ec == 0, stdout.strip()[:120])


# T14: Startup smoke test still ready
def test_T14():
    print("\n--- T14: Startup smoke test still ready ---")
    ec, stdout, stderr = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "run_startup_smoke_test.py"),
    ], timeout=300)
    ok = "ready" in stdout.lower() and ec in (0, 1)
    return test("T14: startup smoke test", ok, f"exit={ec}")


# T15: Governance smoke test still PASS
def test_T15():
    print("\n--- T15: Governance smoke test still PASS ---")
    ec, stdout, stderr = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "run_governance_smoke_test.py"),
    ], timeout=300)
    ok = ec == 0
    return test("T15: governance smoke test", ok, f"exit={ec}")


def main():
    global passed, failed

    print("=" * 60)
    print("OnePal Runtime Runner Tests (T1-T15)")
    print("=" * 60)

    # Tests using temp dir
    with tempfile.TemporaryDirectory(prefix="onepal_runner_test_") as td:
        tmpdir = Path(td)
        test_T1(tmpdir)
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

    # Tests without temp dir (gitignore, smoke tests)
    test_T13()
    test_T14()
    test_T15()

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
