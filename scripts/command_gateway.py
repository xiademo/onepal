#!/usr/bin/env python3
"""OnePal Command Gateway - Task 05-A

Receives commands, routes them deterministically, generates task trees,
and writes MAS trace records.

The Gateway is a SCHEDULING layer — it does NOT execute actions or scripts.
R2+ intents only generate action_ref + waiting_approval status.

Usage:
    py scripts/command_gateway.py --command "run startup smoke test"
    py scripts/command_gateway.py --command "create proposal for memory update"
    py scripts/command_gateway.py --intent read_project_file --target docs/architecture.md
    py scripts/command_gateway.py --command "something unknown"
"""

import argparse
import fnmatch
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROUTES_PATH = PROJECT_ROOT / "workflows" / "coordinator_routes.json"

# Default runtime paths
DEFAULT_COMMANDS_LOG = PROJECT_ROOT / "runtime" / "commands" / "command_requests.jsonl"
DEFAULT_ROUTING_LOG = PROJECT_ROOT / "runtime" / "routing" / "routing_decisions.jsonl"
DEFAULT_TASKS_LOG = PROJECT_ROOT / "runtime" / "tasks" / "tasks.jsonl"
DEFAULT_TREES_LOG = PROJECT_ROOT / "runtime" / "tasks" / "task_trees.jsonl"
DEFAULT_MAS_TRACE = PROJECT_ROOT / "logs" / "mas_trace.jsonl"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def match_route(command_text, routes):
    """Deterministic matching: first pattern match wins."""
    text_lower = command_text.lower().strip()

    for route in routes:
        for pat in route.get("patterns", []):
            pat_lower = pat.lower()
            if fnmatch.fnmatch(text_lower, pat_lower):
                return route

    # Default route
    return {
        "intent": "unknown",
        "route_to": "coordinator_review",
        "risk_level": "R1",
        "owner_agent": "coordinator",
        "execution_type": "review",
        "script_ref": None,
        "action_ref": None,
        "requires_approval": False,
        "requires_manual_review": True,
        "description": "Unknown intent — routed for manual review"
    }


def create_gateway_objects(command_text, route, args, **paths):
    """Create all gateway objects and return summary."""
    command_id = f"cmd_{uuid4().hex[:12]}"
    route_id = f"route_{uuid4().hex[:12]}"
    tree_id = f"tree_{uuid4().hex[:12]}"
    task_id = f"task_{uuid4().hex[:12]}"
    ts = now_iso()

    # Determine status based on risk and execution type
    risk = route.get("risk_level", "R0")
    exec_type = route.get("execution_type", "review")

    if exec_type == "review" or route.get("requires_manual_review"):
        task_status = "draft"  # Held for review
    elif risk in ("R2", "R3", "R4"):
        task_status = "waiting_approval"
    else:
        task_status = "queued"  # Ready to proceed

    tree_status = "planned" if task_status in ("queued",) else "draft"

    # 1. Command Request
    command_req = {
        "command_id": command_id,
        "command_text": command_text,
        "intent": route.get("intent", "unknown"),
        "source": "cli",
        "created_at": ts,
    }
    if "commands_log" in paths:
        append_jsonl(Path(paths["commands_log"]), command_req)

    # 2. Routing Decision
    routing = {
        "routing_decision_id": route_id,
        "command_id": command_id,
        "intent": route.get("intent", "unknown"),
        "route_to": route.get("route_to", "coordinator_review"),
        "execution_type": exec_type,
        "action_ref": route.get("action_ref"),
        "script_ref": route.get("script_ref"),
        "risk_level": risk,
        "requires_approval": route.get("requires_approval", False),
        "requires_manual_review": route.get("requires_manual_review", False),
        "matched_pattern": route.get("description", ""),
        "created_at": ts,
    }
    if "routing_log" in paths:
        append_jsonl(Path(paths["routing_log"]), routing)

    # 3. Task
    task = {
        "task_id": task_id,
        "task_tree_id": tree_id,
        "command_id": command_id,
        "title": command_text[:120],
        "task_type": "command",
        "status": task_status,
        "priority": "P2",
        "owner_agent": route.get("owner_agent", "coordinator"),
        "risk_level": risk,
        "execution_type": exec_type,
        "action_refs": [route["action_ref"]] if route.get("action_ref") else [],
        "script_ref": route.get("script_ref"),
        "created_at": ts,
        "updated_at": None,
    }
    if "tasks_log" in paths:
        append_jsonl(Path(paths["tasks_log"]), task)

    # 4. Task Tree
    tree = {
        "task_tree_id": tree_id,
        "root_task_id": task_id,
        "objective": command_text[:200],
        "owner_agent": route.get("owner_agent", "coordinator"),
        "status": tree_status,
        "task_refs": [task_id],
        "risk_level": risk,
        "created_at": ts,
        "updated_at": None,
    }
    if "trees_log" in paths:
        append_jsonl(Path(paths["trees_log"]), tree)

    # 5. MAS Trace
    trace_entries = [
        {
            "trace_id": f"trace_{uuid4().hex[:8]}",
            "command_id": command_id,
            "event": "command_received",
            "detail": command_text[:200],
            "timestamp": ts,
        },
        {
            "trace_id": f"trace_{uuid4().hex[:8]}",
            "command_id": command_id,
            "routing_decision_id": route_id,
            "event": "routed",
            "detail": f"intent={route.get('intent')}, route_to={route.get('route_to')}",
            "timestamp": ts,
        },
        {
            "trace_id": f"trace_{uuid4().hex[:8]}",
            "command_id": command_id,
            "task_tree_id": tree_id,
            "task_id": task_id,
            "event": "task_tree_created",
            "detail": f"task_tree={tree_id}, status={tree_status}",
            "timestamp": ts,
        },
    ]
    if "mas_trace_log" in paths:
        for entry in trace_entries:
            append_jsonl(Path(paths["mas_trace_log"]), entry)

    return {
        "command_id": command_id,
        "routing_decision_id": route_id,
        "task_tree_id": tree_id,
        "task_id": task_id,
        "intent": route.get("intent", "unknown"),
        "route_to": route.get("route_to", "coordinator_review"),
        "execution_type": exec_type,
        "action_ref": route.get("action_ref"),
        "script_ref": route.get("script_ref"),
        "requires_manual_review": route.get("requires_manual_review", False),
        "status": task_status,
        "risk_level": risk,
    }


def main():
    parser = argparse.ArgumentParser(description="OnePal Command Gateway")
    parser.add_argument("--command", default=None, help="Natural language command")
    parser.add_argument("--intent", default=None, help="Explicit intent override")
    parser.add_argument("--target", default=None, help="Target (e.g. file path)")
    parser.add_argument("--profile", default="safe_readonly", help="Profile ID")
    parser.add_argument("--commands-log", default=None, help="Command requests JSONL path")
    parser.add_argument("--routing-log", default=None, help="Routing decisions JSONL path")
    parser.add_argument("--tasks-log", default=None, help="Tasks JSONL path")
    parser.add_argument("--task-trees-log", default=None, help="Task trees JSONL path")
    parser.add_argument("--mas-trace-log", default=None, help="MAS trace JSONL path")
    args = parser.parse_args()

    command_text = args.command or args.intent or ""
    if not command_text:
        print(json.dumps({"error": "provide --command or --intent"}, ensure_ascii=False))
        sys.exit(1)

    # Load routes
    routes_data = load_json(ROUTES_PATH)
    command_routes = routes_data.get("command_routes", [])
    default_route = routes_data.get("default_route", {})

    # Build route list with default fallback
    all_routes = list(command_routes) + [default_route]

    # Match route
    route = match_route(command_text, all_routes)

    # Prepare paths
    paths = {}
    if args.commands_log:
        paths["commands_log"] = args.commands_log
    if args.routing_log:
        paths["routing_log"] = args.routing_log
    if args.tasks_log:
        paths["tasks_log"] = args.tasks_log
    if args.task_trees_log:
        paths["trees_log"] = args.task_trees_log
    if args.mas_trace_log:
        paths["mas_trace_log"] = args.mas_trace_log

    # Create all objects
    result = create_gateway_objects(command_text, route, args, **paths)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit 0: routing successful (even if manual review needed)
    sys.exit(0)


if __name__ == "__main__":
    main()
