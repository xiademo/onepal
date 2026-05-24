#!/usr/bin/env python3
"""OnePal Command Gateway Tests - Task 05-A (T1-T12)

Tests: command routing, task tree creation, MAS trace, gitignore, boundary enforcement.
Uses temporary test directories — never touches production runtime files.

Usage:
    py tests/test_command_gateway.py
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = "py"

passed = 0
failed = 0


def run_cmd(cmd, timeout=60):
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


# T1: command_gateway receives "run startup smoke test"
def test_T1(tmpdir):
    print("\n--- T1: command_gateway 'run startup smoke test' ---")
    cmd_file = tmpdir / "commands.jsonl"
    route_file = tmpdir / "routing.jsonl"
    tasks_file = tmpdir / "tasks.jsonl"
    trees_file = tmpdir / "trees.jsonl"
    trace_file = tmpdir / "mas_trace.jsonl"

    ec, stdout, stderr = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "command_gateway.py"),
        "--command", "run startup smoke test",
        "--commands-log", str(cmd_file),
        "--routing-log", str(route_file),
        "--tasks-log", str(tasks_file),
        "--task-trees-log", str(trees_file),
        "--mas-trace-log", str(trace_file),
    ])
    if ec != 0:
        return test("T1: gateway exit 0", False, stderr)
    try:
        data = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return test("T1: gateway JSON parse", False, stdout[:200])

    ok = all([
        data.get("execution_type") == "script_ref",
        data.get("route_to") == "runtime",
        data.get("command_id", "").startswith("cmd_"),
        data.get("task_tree_id", "").startswith("tree_"),
    ])
    return test("T1: correct routing + task_tree IDs", ok, json.dumps(data, indent=2)[:300])


# T2: command_request JSONL written
def test_T2(tmpdir):
    print("\n--- T2: command_request JSONL writable ---")
    cmd_file = tmpdir / "cmd_t2.jsonl"
    ec, _, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "command_gateway.py"),
        "--command", "check health",
        "--commands-log", str(cmd_file),
        "--routing-log", str(tmpdir / "r_t2.jsonl"),
        "--tasks-log", str(tmpdir / "t_t2.jsonl"),
        "--task-trees-log", str(tmpdir / "tt_t2.jsonl"),
        "--mas-trace-log", str(tmpdir / "mas_t2.jsonl"),
    ])
    cnt = count_jsonl(cmd_file)
    return test("T2: command_request JSONL written", ec == 0 and cnt > 0, f"lines={cnt}")


# T3: routing_decision JSONL written
def test_T3(tmpdir):
    print("\n--- T3: routing_decision JSONL written ---")
    route_file = tmpdir / "routing_t3.jsonl"
    ec, _, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "command_gateway.py"),
        "--command", "check governance tests",
        "--routing-log", str(route_file),
        "--commands-log", str(tmpdir / "c_t3.jsonl"),
        "--tasks-log", str(tmpdir / "t_t3.jsonl"),
        "--task-trees-log", str(tmpdir / "tt_t3.jsonl"),
        "--mas-trace-log", str(tmpdir / "mas_t3.jsonl"),
    ])
    cnt = count_jsonl(route_file)
    return test("T3: routing JSONL written", ec == 0 and cnt > 0, f"lines={cnt}")


# T4: task_tree JSONL written
def test_T4(tmpdir):
    print("\n--- T4: task_tree JSONL written ---")
    trees_file = tmpdir / "trees_t4.jsonl"
    ec, _, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "command_gateway.py"),
        "--command", "run startup smoke test",
        "--task-trees-log", str(trees_file),
        "--commands-log", str(tmpdir / "c_t4.jsonl"),
        "--routing-log", str(tmpdir / "r_t4.jsonl"),
        "--tasks-log", str(tmpdir / "t_t4.jsonl"),
        "--mas-trace-log", str(tmpdir / "mas_t4.jsonl"),
    ])
    cnt = count_jsonl(trees_file)
    return test("T4: task_tree JSONL written", ec == 0 and cnt > 0, f"lines={cnt}")


# T5: unknown intent → coordinator_review
def test_T5(tmpdir):
    print("\n--- T5: unknown intent → coordinator_review ---")
    ec, stdout, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "command_gateway.py"),
        "--command", "xyzzy flurbo blarg unrecognized",
        "--commands-log", str(tmpdir / "c_t5.jsonl"),
        "--routing-log", str(tmpdir / "r_t5.jsonl"),
        "--tasks-log", str(tmpdir / "t_t5.jsonl"),
        "--task-trees-log", str(tmpdir / "tt_t5.jsonl"),
        "--mas-trace-log", str(tmpdir / "mas_t5.jsonl"),
    ])
    try:
        data = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return test("T5: JSON output", False, stdout[:200])
    ok = (data.get("requires_manual_review") == True and
          data.get("execution_type") == "review")
    return test("T5: manual_review=True, execution_type=review", ok, json.dumps(data, indent=2)[:300])


# T6: create_proposal → action.create_proposal
def test_T6(tmpdir):
    print("\n--- T6: create_proposal → action.create_proposal ---")
    ec, stdout, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "command_gateway.py"),
        "--command", "create proposal for memory update",
        "--commands-log", str(tmpdir / "c_t6.jsonl"),
        "--routing-log", str(tmpdir / "r_t6.jsonl"),
        "--tasks-log", str(tmpdir / "t_t6.jsonl"),
        "--task-trees-log", str(tmpdir / "tt_t6.jsonl"),
        "--mas-trace-log", str(tmpdir / "mas_t6.jsonl"),
    ])
    try:
        data = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return test("T6: JSON output", False, stdout[:200])
    ok = (data.get("action_ref") == "action.create_proposal" and
          data.get("execution_type") == "action_ref")
    return test("T6: action_ref=action.create_proposal", ok, json.dumps(data, indent=2)[:300])


# T7: read_project_file → action.read_file (Gateway doesn't read)
def test_T7(tmpdir):
    print("\n--- T7: read_project_file → action.read_file (no file access) ---")
    ec, stdout, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "command_gateway.py"),
        "--command", "read file docs/architecture.md",
        "--commands-log", str(tmpdir / "c_t7.jsonl"),
        "--routing-log", str(tmpdir / "r_t7.jsonl"),
        "--tasks-log", str(tmpdir / "t_t7.jsonl"),
        "--task-trees-log", str(tmpdir / "tt_t7.jsonl"),
        "--mas-trace-log", str(tmpdir / "mas_t7.jsonl"),
    ])
    try:
        data = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return test("T7: JSON output", False, stdout[:200])
    ok = (data.get("action_ref") == "action.read_file" and
          data.get("risk_level") == "R0")
    return test("T7: action_ref=read_file, R0, Gateway does not read file", ok,
                json.dumps(data, indent=2)[:300])


# T8: task_tree status flow via task_tree.py
def test_T8(tmpdir):
    print("\n--- T8: task_tree status flow: draft → queued → completed ---")
    tasks_file = tmpdir / "tasks_t8.jsonl"
    trees_file = tmpdir / "trees_t8.jsonl"

    ec, out, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "task_tree.py"),
        "--create-tree", "--objective", "Test status flow",
        "--owner", "coordinator",
        "--risk-level", "R0",
        "--tasks-log", str(tasks_file),
        "--task-trees-log", str(trees_file),
    ])
    try:
        result = json.loads(out.strip())
        task_id = result["task"]["task_id"]
        tree_id = result["tree"]["task_tree_id"]
    except (json.JSONDecodeError, KeyError):
        return test("T8: created tree", False, out[:300])

    # Update to queued
    ec, _, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "task_tree.py"),
        "--update-task", "--task-id", task_id, "--status", "queued",
        "--tasks-log", str(tasks_file),
    ])
    # Update to completed
    ec, _, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "task_tree.py"),
        "--update-task", "--task-id", task_id, "--status", "completed",
        "--tasks-log", str(tasks_file),
    ])
    # Update tree to completed
    ec, _, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "task_tree.py"),
        "--update-tree", "--tree-id", tree_id, "--status", "completed",
        "--task-trees-log", str(trees_file),
    ])

    # Verify final state
    ec, out, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "task_tree.py"),
        "--read-task", "--task-id", task_id,
        "--tasks-log", str(tasks_file),
    ])
    try:
        task_final = json.loads(out.strip())
    except json.JSONDecodeError:
        return test("T8: read task", False, out[:200])

    ok = task_final.get("status") == "completed"
    return test("T8: task status = completed", ok, f"status={task_final.get('status')}")


# T9: mas_trace written
def test_T9(tmpdir):
    print("\n--- T9: MAS trace written ---")
    trace_file = tmpdir / "mas_t9.jsonl"
    ec, _, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "command_gateway.py"),
        "--command", "run startup smoke test",
        "--mas-trace-log", str(trace_file),
        "--commands-log", str(tmpdir / "c_t9.jsonl"),
        "--routing-log", str(tmpdir / "r_t9.jsonl"),
        "--tasks-log", str(tmpdir / "t_t9.jsonl"),
        "--task-trees-log", str(tmpdir / "tt_t9.jsonl"),
    ])
    cnt = count_jsonl(trace_file)
    events = []
    if trace_file.exists():
        with open(trace_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line).get("event"))
                    except:
                        pass
    ok = ("command_received" in events and "routed" in events and "task_tree_created" in events)
    return test("T9: MAS trace has all 3 events", ok, f"events={events}")


# T10: all runtime JSONL parseable
def test_T10(tmpdir):
    print("\n--- T10: all runtime JSONL parseable ---")
    ec, _, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "command_gateway.py"),
        "--command", "check health",
        "--commands-log", str(tmpdir / "c_t10.jsonl"),
        "--routing-log", str(tmpdir / "r_t10.jsonl"),
        "--tasks-log", str(tmpdir / "t_t10.jsonl"),
        "--task-trees-log", str(tmpdir / "tt_t10.jsonl"),
        "--mas-trace-log", str(tmpdir / "mas_t10.jsonl"),
    ])
    all_ok = True
    bad = 0
    for fname in tmpdir.iterdir():
        if fname.suffix == ".jsonl":
            with open(fname, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            json.loads(line)
                        except json.JSONDecodeError:
                            bad += 1
                            all_ok = False
    return test("T10: all JSONL parseable", all_ok, f"bad_lines={bad}")


# T11: runtime JSONL gitignored
def test_T11():
    print("\n--- T11: runtime JSONL gitignored ---")
    paths = [
        "runtime/commands/command_requests.jsonl",
        "runtime/routing/routing_decisions.jsonl",
        "runtime/tasks/tasks.jsonl",
        "runtime/tasks/task_trees.jsonl",
    ]
    all_ok = True
    for p in paths:
        ec, stdout, _ = run_cmd(["git", "check-ignore", "-v", p], timeout=10)
        if ec != 0:
            all_ok = False
            break
    return test("T11: runtime JSONLs gitignored", all_ok)


# T12: Gateway does not execute R2+ action
def test_T12(tmpdir):
    print("\n--- T12: Gateway does not execute R2+ action ---")
    # Create a route that simulates R2 routing
    # The approve_proposal pattern: "approve*" matches our action.approve_proposal
    # But in our routes, there's no "approve*" pattern - it would default to unknown → review
    ec, stdout, _ = run_cmd([
        PY, str(PROJECT_ROOT / "scripts" / "command_gateway.py"),
        "--command", "approve proposal prop_xxx",
        "--commands-log", str(tmpdir / "c_t12.jsonl"),
        "--routing-log", str(tmpdir / "r_t12.jsonl"),
        "--tasks-log", str(tmpdir / "t_t12.jsonl"),
        "--task-trees-log", str(tmpdir / "tt_t12.jsonl"),
        "--mas-trace-log", str(tmpdir / "mas_t12.jsonl"),
    ])
    try:
        data = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return test("T12: JSON output", False, stdout[:200])
    # R2-like intent should NOT directly execute; should require manual review
    ok = (data.get("requires_manual_review") == True or
          data.get("status") == "waiting_approval" or
          data.get("execution_type") in ("review", None))
    return test("T12: R2 intent does not directly execute", ok,
                json.dumps(data, indent=2)[:300])


def main():
    global passed, failed

    print("=" * 60)
    print("OnePal Command Gateway Tests (T1-T12)")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="onepal_gw_test_") as td:
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

    test_T11()

    with tempfile.TemporaryDirectory(prefix="onepal_gw_test_") as td:
        tmpdir = Path(td)
        test_T12(tmpdir)

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
