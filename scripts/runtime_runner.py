#!/usr/bin/env python3
"""OnePal Runtime Runner - Task 05-B

Controlled execution bridge. Reads queued tasks and executes them under
strict allowlist constraints. Delegates action_ref to request_action.py.
Does NOT bypass governance.

Usage:
    py scripts/runtime_runner.py --run-next
    py scripts/runtime_runner.py --task-id task_xxx
    py scripts/runtime_runner.py --dry-run
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ALLOWLIST_PATH = PROJECT_ROOT / "workflows" / "runtime_execution_allowlist.json"
TASKS_LOG = PROJECT_ROOT / "runtime" / "tasks" / "tasks.jsonl"
TREES_LOG = PROJECT_ROOT / "runtime" / "tasks" / "task_trees.jsonl"
TASK_RUNS_LOG = PROJECT_ROOT / "runtime" / "task_runs" / "task_runs.jsonl"
MAS_TRACE = PROJECT_ROOT / "logs" / "mas_trace.jsonl"
REQUEST_ACTION = PROJECT_ROOT / "scripts" / "request_action.py"

PY = "py"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_trace(event, mas_trace_path, command_id=None, task_id=None, tree_id=None, detail=""):
    entry = {
        "trace_id": f"trace_{uuid4().hex[:8]}",
        "command_id": command_id,
        "task_tree_id": tree_id,
        "task_id": task_id,
        "event": event,
        "detail": detail[:300],
        "timestamp": now_iso(),
    }
    append_jsonl(mas_trace_path, entry)
    return entry


def check_allowlist(allowlist, task):
    """Validate task against allowlist. Returns (ok, reason)."""
    exec_type = task.get("execution_type", "")
    script_ref = task.get("script_ref", "")
    action_refs = task.get("action_refs", [])

    if exec_type == "script_ref":
        if not script_ref:
            return False, "script_ref is empty"
        # Forbidden extensions
        for ext in allowlist.get("forbidden_extensions", []):
            if script_ref.endswith(ext):
                return False, f"forbidden extension: {ext}"
        # Forbidden paths
        for bad in allowlist.get("forbidden_paths", []):
            if bad in script_ref:
                return False, f"forbidden path pattern: {bad}"
        # Must be in allowed_scripts
        if script_ref not in allowlist.get("allowed_scripts", []):
            return False, f"script not allowlisted: {script_ref}"
        # Must exist
        script_path = PROJECT_ROOT / script_ref
        if not script_path.exists():
            return False, f"script not found: {script_ref}"
        return True, "allowlisted"

    if exec_type == "action_ref":
        if not action_refs:
            return False, "action_refs is empty"
        # Check that at least one action_ref is in allowed_actions
        allowed = allowlist.get("allowed_actions", [])
        for ar in action_refs:
            if ar in allowed:
                return True, f"action_ref allowlisted: {ar}"
        return False, f"no action_ref in allowlist: {action_refs}"

    if exec_type == "review":
        return False, "review — not executable"

    return False, f"unknown execution_type: {exec_type}"


def run_script(task, dry_run, mas_trace_path):
    """Execute an allowlisted Python script via subprocess."""
    script_ref = task["script_ref"]
    script_path = PROJECT_ROOT / script_ref
    cmd = [PY, str(script_path)]
    if dry_run:
        cmd.append("--dry-run")

    append_trace("runner_script_start", mas_trace_path, task.get("command_id"), task["task_id"],
                 task.get("task_tree_id"), f"script={script_ref} dry_run={dry_run}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=300, encoding="utf-8", errors="replace")
        return {
            "exit_code": result.returncode,
            "stdout": (result.stdout or "")[:2000],
            "stderr": (result.stderr or "")[:500],
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "timeout"}


def run_action(task, dry_run, mas_trace_path):
    """Delegate action_ref to request_action.py via subprocess."""
    action_refs = task.get("action_refs", [])
    action_id = action_refs[0] if action_refs else ""
    profile = "safe_readonly"
    cmd = [PY, str(REQUEST_ACTION), "--action", action_id, "--profile", profile]
    if dry_run:
        cmd.append("--dry-run")

    append_trace("runner_action_delegate", mas_trace_path, task.get("command_id"), task["task_id"],
                 task.get("task_tree_id"), f"action={action_id} dry_run={dry_run}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=120, encoding="utf-8", errors="replace")
        return {
            "exit_code": result.returncode,
            "stdout": (result.stdout or "")[:2000],
            "stderr": (result.stderr or "")[:500],
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "timeout"}


def update_task_status(task_id, new_status, tasks_path):
    """Update task status in tasks.jsonl."""
    tasks = load_jsonl(tasks_path)
    for i, t in enumerate(tasks):
        if t.get("task_id") == task_id:
            tasks[i]["status"] = new_status
            tasks[i]["updated_at"] = now_iso()
            write_jsonl(tasks_path, tasks)
            return True
    return False


def process_task(task, allowlist, dry_run, tasks_path, trees_path, task_runs_path, mas_trace_path):
    """Process a single queued task. Returns task_run record."""
    task_id = task.get("task_id", "unknown")
    tree_id = task.get("task_tree_id", "")
    cmd_id = task.get("command_id", "")
    exec_type = task.get("execution_type", "review")

    task_run = {
        "task_run_id": f"taskrun_{uuid4().hex[:12]}",
        "task_id": task_id,
        "task_tree_id": tree_id,
        "command_id": cmd_id,
        "execution_type": exec_type,
        "action_ref": task.get("action_refs", [None])[0] if task.get("action_refs") else None,
        "script_ref": task.get("script_ref"),
        "dry_run": dry_run,
        "started_at": now_iso(),
        "completed_at": None,
        "exit_code": None,
        "stdout_summary": "",
        "stderr_summary": "",
        "error": None,
        "created_at": now_iso(),
    }

    # Allowlist check
    ok, reason = check_allowlist(allowlist, task)
    if not ok:
        task_run["status"] = "rejected"
        task_run["error"] = reason
        task_run["completed_at"] = now_iso()
        append_jsonl(task_runs_path, task_run)
        append_trace("runner_rejected", mas_trace_path, cmd_id, task_id, tree_id, reason)
        update_task_status(task_id, "waiting_review" if exec_type == "review" else "failed", tasks_path)
        return task_run

    # Update to running
    update_task_status(task_id, "running", tasks_path)
    append_trace("runner_executing", mas_trace_path, cmd_id, task_id, tree_id,
                 f"exec_type={exec_type} dry_run={dry_run}")

    # Execute
    if exec_type == "script_ref":
        exec_result = run_script(task, dry_run, mas_trace_path)
    elif exec_type == "action_ref":
        exec_result = run_action(task, dry_run, mas_trace_path)
    else:
        task_run["status"] = "rejected"
        task_run["error"] = f"cannot execute type: {exec_type}"
        task_run["completed_at"] = now_iso()
        append_jsonl(task_runs_path, task_run)
        return task_run

    # Record result
    exit_code = exec_result["exit_code"]
    task_run["exit_code"] = exit_code
    task_run["stdout_summary"] = exec_result["stdout"][:500]
    task_run["stderr_summary"] = exec_result["stderr"][:500]
    task_run["completed_at"] = now_iso()

    if exit_code == 0:
        task_run["status"] = "completed"
        update_task_status(task_id, "completed", tasks_path)
        append_trace("runner_completed", mas_trace_path, cmd_id, task_id, tree_id,
                     f"exit={exit_code}")
    else:
        task_run["status"] = "failed"
        task_run["error"] = exec_result["stderr"][:200]
        update_task_status(task_id, "failed", tasks_path)
        append_trace("runner_failed", mas_trace_path, cmd_id, task_id, tree_id,
                     f"exit={exit_code}")

    append_jsonl(task_runs_path, task_run)
    return task_run

    # Update to running
    update_task_status(task_id, "running")
    append_trace("runner_executing", cmd_id, task_id, tree_id,
                 f"exec_type={exec_type} dry_run={dry_run}")

    # Execute
    if exec_type == "script_ref":
        exec_result = run_script(task, dry_run)
    elif exec_type == "action_ref":
        exec_result = run_action(task, dry_run)
    else:
        task_run["status"] = "rejected"
        task_run["error"] = f"cannot execute type: {exec_type}"
        task_run["completed_at"] = now_iso()
        append_jsonl(TASK_RUNS_LOG, task_run)
        return task_run

    # Record result
    exit_code = exec_result["exit_code"]
    task_run["exit_code"] = exit_code
    task_run["stdout_summary"] = exec_result["stdout"][:500]
    task_run["stderr_summary"] = exec_result["stderr"][:500]
    task_run["completed_at"] = now_iso()

    if exit_code == 0:
        task_run["status"] = "completed"
        update_task_status(task_id, "completed")
        append_trace("runner_completed", cmd_id, task_id, tree_id,
                     f"exit={exit_code}")
    else:
        task_run["status"] = "failed"
        task_run["error"] = exec_result["stderr"][:200]
        update_task_status(task_id, "failed")
        append_trace("runner_failed", cmd_id, task_id, tree_id,
                     f"exit={exit_code}")

    append_jsonl(TASK_RUNS_LOG, task_run)
    return task_run


def main():
    parser = argparse.ArgumentParser(description="OnePal Runtime Runner")
    parser.add_argument("--run-next", action="store_true", help="Run the next queued task")
    parser.add_argument("--task-id", default=None, help="Run a specific task by ID")
    parser.add_argument("--dry-run", action="store_true", help="Execute in dry-run mode")
    parser.add_argument("--tasks-log", default=None, help="Path to tasks.jsonl")
    parser.add_argument("--trees-log", default=None, help="Path to task_trees.jsonl")
    parser.add_argument("--task-runs-log", default=None, help="Path to task_runs.jsonl")
    parser.add_argument("--mas-trace-log", default=None, help="Path to mas_trace.jsonl")
    parser.add_argument("--allowlist", default=None, help="Path to allowlist config")
    args = parser.parse_args()

    if not args.run_next and not args.task_id:
        print(json.dumps({"error": "provide --run-next or --task-id"}, ensure_ascii=False))
        sys.exit(1)

    # Resolve paths
    tasks_path = Path(args.tasks_log) if args.tasks_log else TASKS_LOG
    trees_path = Path(args.trees_log) if args.trees_log else TREES_LOG
    task_runs_path = Path(args.task_runs_log) if args.task_runs_log else TASK_RUNS_LOG
    mas_trace_path = Path(args.mas_trace_log) if args.mas_trace_log else MAS_TRACE
    allowlist_path = Path(args.allowlist) if args.allowlist else ALLOWLIST_PATH

    # Load allowlist
    try:
        allowlist = load_json(allowlist_path)
    except (FileNotFoundError, json.JSONDecodeError):
        print(json.dumps({"error": "cannot load allowlist"}, ensure_ascii=False))
        sys.exit(1)

    dry_run = args.dry_run or allowlist.get("default_dry_run", True)

    # Load tasks
    tasks = load_jsonl(tasks_path)
    queued = [t for t in tasks if t.get("status") == "queued"]

    if args.task_id:
        target = [t for t in tasks if t.get("task_id") == args.task_id]
        if not target:
            print(json.dumps({"error": f"task '{args.task_id}' not found"}, ensure_ascii=False))
            sys.exit(1)
        task_run = process_task(target[0], allowlist, dry_run, tasks_path, trees_path, task_runs_path, mas_trace_path)
        print(json.dumps(task_run, indent=2, ensure_ascii=False))
        sys.exit(0 if task_run.get("status") == "completed" else 1)

    if args.run_next:
        if not queued:
            print(json.dumps({"status": "no_queued_tasks"}, ensure_ascii=False))
            sys.exit(0)

        # Sort by created_at, pick first
        queued.sort(key=lambda t: t.get("created_at", ""))
        task_run = process_task(queued[0], allowlist, dry_run, tasks_path, trees_path, task_runs_path, mas_trace_path)
        print(json.dumps(task_run, indent=2, ensure_ascii=False))
        sys.exit(0 if task_run.get("status") == "completed" else 1)


if __name__ == "__main__":
    main()
