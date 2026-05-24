#!/usr/bin/env python3
"""OnePal Task Tree Manager - Task 05-A

CRUD operations for tasks and task trees.
Uses task.schema.json and task_tree.schema.json compliant status values.

Status mapping:
  created → draft    routed → queued    executing → running

Usage:
    py scripts/task_tree.py --create-tree --objective "..." --owner coordinator
    py scripts/task_tree.py --add-task --tree-id <id> --title "..." --task-type build
    py scripts/task_tree.py --update-task --task-id <id> --status completed
    py scripts/task_tree.py --update-tree --tree-id <id> --status completed
    py scripts/task_tree.py --read-tree --tree-id <id>
    py scripts/task_tree.py --read-task --task-id <id>
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASKS_LOG = PROJECT_ROOT / "runtime" / "tasks" / "tasks.jsonl"
DEFAULT_TREES_LOG = PROJECT_ROOT / "runtime" / "tasks" / "task_trees.jsonl"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


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


def append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def find_by_id(records, record_id, id_field):
    for i, r in enumerate(records):
        if r.get(id_field) == record_id:
            return i, r
    return None, None


def create_task_tree(objective, owner, risk_level, tasks_log, trees_log, **extra):
    tree_id = f"tree_{uuid4().hex[:12]}"
    task_id = f"task_{uuid4().hex[:12]}"

    task = {
        "task_id": task_id,
        "task_tree_id": tree_id,
        "title": objective,
        "task_type": extra.get("task_type", "command"),
        "status": "draft",
        "priority": extra.get("priority", "P2"),
        "owner_agent": owner,
        "risk_level": risk_level,
        "created_at": now_iso(),
        "updated_at": None,
    }
    append_jsonl(tasks_log, task)

    tree = {
        "task_tree_id": tree_id,
        "root_task_id": task_id,
        "objective": objective,
        "owner_agent": owner,
        "status": "draft",
        "task_refs": [task_id],
        "risk_level": risk_level,
        "created_at": now_iso(),
        "updated_at": None,
    }
    append_jsonl(trees_log, tree)

    return {"task": task, "tree": tree}


def update_task(task_id, new_status, tasks_log, **fields):
    records = load_jsonl(tasks_log)
    idx, task = find_by_id(records, task_id, "task_id")
    if idx is None or task is None:
        return None
    task["status"] = new_status
    task["updated_at"] = now_iso()
    for k, v in fields.items():
        task[k] = v
    records[idx] = task
    write_jsonl(tasks_log, records)
    return task


def update_tree(tree_id, new_status, trees_log, **fields):
    records = load_jsonl(trees_log)
    idx, tree = find_by_id(records, tree_id, "task_tree_id")
    if idx is None or tree is None:
        return None
    tree["status"] = new_status
    tree["updated_at"] = now_iso()
    for k, v in fields.items():
        tree[k] = v
    records[idx] = tree
    write_jsonl(trees_log, records)
    return tree


def add_child_task(tree_id, title, task_type, parent_task_id, tasks_log, trees_log, **extra):
    task_id = f"task_{uuid4().hex[:12]}"
    task = {
        "task_id": task_id,
        "task_tree_id": tree_id,
        "parent_task_id": parent_task_id,
        "title": title,
        "task_type": task_type,
        "status": "draft",
        "priority": extra.get("priority", "P2"),
        "owner_agent": extra.get("owner_agent", "coordinator"),
        "risk_level": extra.get("risk_level", "R0"),
        "created_at": now_iso(),
        "updated_at": None,
    }
    append_jsonl(tasks_log, task)

    # Update tree task_refs
    trees = load_jsonl(trees_log)
    idx, tree = find_by_id(trees, tree_id, "task_tree_id")
    if idx is not None and tree is not None:
        refs = tree.get("task_refs", [])
        refs.append(task_id)
        tree["task_refs"] = refs
        tree["updated_at"] = now_iso()
        trees[idx] = tree
        write_jsonl(trees_log, trees)

    return task


def main():
    parser = argparse.ArgumentParser(description="OnePal Task Tree Manager")
    parser.add_argument("--create-tree", action="store_true", help="Create a new task tree")
    parser.add_argument("--add-task", action="store_true", help="Add a child task")
    parser.add_argument("--update-task", action="store_true", help="Update task status")
    parser.add_argument("--update-tree", action="store_true", help="Update tree status")
    parser.add_argument("--read-tree", action="store_true", help="Read a task tree")
    parser.add_argument("--read-task", action="store_true", help="Read a task")
    parser.add_argument("--objective", default=None, help="Objective / title")
    parser.add_argument("--owner", default="coordinator", help="Owner agent")
    parser.add_argument("--tree-id", default=None, help="Task tree ID")
    parser.add_argument("--task-id", default=None, help="Task ID")
    parser.add_argument("--parent-task-id", default=None, help="Parent task ID")
    parser.add_argument("--title", default=None, help="Task title")
    parser.add_argument("--task-type", default="command", help="Task type")
    parser.add_argument("--status", default=None, help="New status")
    parser.add_argument("--risk-level", default="R0", help="Risk level")
    parser.add_argument("--priority", default="P2", help="Priority")
    parser.add_argument("--tasks-log", default=None, help="Path to tasks.jsonl")
    parser.add_argument("--task-trees-log", default=None, help="Path to task_trees.jsonl")
    args = parser.parse_args()

    tasks_path = Path(args.tasks_log) if args.tasks_log else DEFAULT_TASKS_LOG
    trees_path = Path(args.task_trees_log) if args.task_trees_log else DEFAULT_TREES_LOG

    if args.create_tree:
        if not args.objective:
            print(json.dumps({"error": "--objective is required for --create-tree"}))
            sys.exit(1)
        result = create_task_tree(args.objective, args.owner, args.risk_level,
                                   tasks_path, trees_path,
                                   task_type=args.task_type, priority=args.priority)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.add_task:
        if not args.tree_id or not args.title:
            print(json.dumps({"error": "--tree-id and --title are required for --add-task"}))
            sys.exit(1)
        result = add_child_task(args.tree_id, args.title, args.task_type,
                                args.parent_task_id or args.tree_id, tasks_path, trees_path,
                                owner_agent=args.owner, risk_level=args.risk_level)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.update_task:
        if not args.task_id or not args.status:
            print(json.dumps({"error": "--task-id and --status are required for --update-task"}))
            sys.exit(1)
        result = update_task(args.task_id, args.status, tasks_path)
        if result is None:
            print(json.dumps({"error": f"task '{args.task_id}' not found"}))
            sys.exit(1)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.update_tree:
        if not args.tree_id or not args.status:
            print(json.dumps({"error": "--tree-id and --status are required for --update-tree"}))
            sys.exit(1)
        result = update_tree(args.tree_id, args.status, trees_path)
        if result is None:
            print(json.dumps({"error": f"tree '{args.tree_id}' not found"}))
            sys.exit(1)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.read_tree:
        if not args.tree_id:
            print(json.dumps({"error": "--tree-id is required for --read-tree"}))
            sys.exit(1)
        records = load_jsonl(trees_path)
        _, tree = find_by_id(records, args.tree_id, "task_tree_id")
        if tree is None:
            print(json.dumps({"error": f"tree '{args.tree_id}' not found"}))
            sys.exit(1)
        print(json.dumps(tree, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.read_task:
        if not args.task_id:
            print(json.dumps({"error": "--task-id is required for --read-task"}))
            sys.exit(1)
        records = load_jsonl(tasks_path)
        _, task = find_by_id(records, args.task_id, "task_id")
        if task is None:
            print(json.dumps({"error": f"task '{args.task_id}' not found"}))
            sys.exit(1)
        print(json.dumps(task, indent=2, ensure_ascii=False))
        sys.exit(0)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
