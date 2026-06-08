#!/usr/bin/env python3
"""OnePal Readiness Center - Tasks 16-20.

Local readiness records for Automation, Skill lifecycle, Knowledge Graph,
Model/Cost, and MCP/Tool governance. It never starts services, enables MCP,
routes models through LiteLLM, runs RAG, or performs external actions.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKFLOWS = ROOT / "automation" / "workflows" / "automation_workflows.jsonl"
DEFAULT_RUNS = ROOT / "automation" / "runs" / "workflow_runs.jsonl"
DEFAULT_SKILLS = ROOT / "capabilities" / "skills" / "skill_candidates.jsonl"
DEFAULT_SKILL_REVIEWS = ROOT / "capabilities" / "skills" / "skill_reviews.jsonl"
DEFAULT_NODES = ROOT / "knowledge_graph" / "nodes.jsonl"
DEFAULT_EDGES = ROOT / "knowledge_graph" / "edges.jsonl"
DEFAULT_BOUNDARIES = ROOT / "knowledge_graph" / "boundaries.jsonl"
DEFAULT_KSTATE = ROOT / "knowledge_graph" / "state.jsonl"
DEFAULT_MODEL_ROUTES = ROOT / "model_cost" / "model_routes.jsonl"
DEFAULT_COST_EVENTS = ROOT / "model_cost" / "cost_events.jsonl"
DEFAULT_MCP_PROFILES = ROOT / "mcp" / "profiles" / "mcp_server_profiles.jsonl"
DEFAULT_TOOL_POLICIES = ROOT / "mcp" / "policies" / "tool_trust_policies.jsonl"
DEFAULT_AUDIT = ROOT / "logs" / "readiness_audit.jsonl"

SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{10,}",
    r"-----BEGIN",
    r"ghp_[a-zA-Z0-9]{20,}",
    r"(?:api[_-]?key|password|token|secret)\s*[:=]\s*\S{8,}",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def audit(action, detail, audit_path, **refs):
    entry = {
        "audit_id": f"audit_{uuid4().hex[:12]}",
        "action": action,
        "detail": detail[:300],
        "timestamp": now_iso(),
    }
    entry.update({k: v for k, v in refs.items() if v})
    append_jsonl(audit_path, entry)


def fail(message, status="error"):
    print(json.dumps({"status": status, "error": message}, ensure_ascii=False))
    sys.exit(1)


def csv(value):
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def csv_text(value):
    return ",".join(csv(value))


def has_secret(*values):
    text = " ".join(str(v or "") for v in values)
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in SECRET_PATTERNS)


def find(rows, key, value):
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def workflow_create(args, workflows_path, audit_path):
    if not args.name.strip():
        fail("name required")
    if has_secret(args.name):
        fail("secret-like content rejected", "rejected")
    workflow = {
        "workflow_id": f"wf_{uuid4().hex[:12]}",
        "name": args.name.strip(),
        "owner_agent": args.owner_agent,
        "enabled": False,
        "risk_level": args.risk_level,
        "trigger_type": args.trigger_type,
        "schedule_ref": args.schedule_ref,
        "action_refs": csv(args.action_refs),
        "required_secret_refs": [],
        "allowed_profiles": ["safe_readonly"],
        "approval_required": True,
        "rate_limit": {"mode": "manual_preflight"},
        "rollback_supported": False,
        "status": "draft",
    }
    append_jsonl(workflows_path, workflow)
    audit("workflow_readiness_created", f"workflow={workflow['workflow_id']}", audit_path, workflow_id=workflow["workflow_id"])
    print(json.dumps({"status": "created", "workflow": workflow, "note": "disabled by default"}, indent=2, ensure_ascii=False))


def workflow_trigger(args, workflows_path, runs_path, audit_path):
    workflow = find(load_jsonl(workflows_path), "workflow_id", args.workflow_id)
    if workflow is None:
        fail(f"workflow '{args.workflow_id}' not found", "not_found")
    run = {
        "workflow_run_id": f"wfrun_{uuid4().hex[:12]}",
        "workflow_id": args.workflow_id,
        "triggered_by": args.triggered_by,
        "status": "preflight",
        "input_refs": csv(args.input_refs),
        "output_refs": ["approval_required", "not_executed"],
        "error_type": None,
        "started_at": now_iso(),
        "ended_at": None,
    }
    append_jsonl(runs_path, run)
    audit("workflow_preflight_created", f"run={run['workflow_run_id']}", audit_path, workflow_run_id=run["workflow_run_id"])
    print(json.dumps({"status": "created", "run": run, "note": "preflight only; no action executed"}, indent=2, ensure_ascii=False))


def skill_candidate(args, skills_path, audit_path):
    if not args.name.strip():
        fail("name required")
    if has_secret(args.name, args.description):
        fail("secret-like content rejected", "rejected")
    skill = {
        "skill_id": f"skill_{uuid4().hex[:12]}",
        "name": args.name.strip(),
        "version": "0.1.0",
        "owner_agent": args.owner_agent,
        "description": args.description,
        "trigger_conditions": csv(args.trigger_conditions),
        "input_schema_ref": args.input_schema_ref,
        "output_schema_ref": args.output_schema_ref,
        "required_actions": csv(args.required_actions),
        "permission_required": args.permission_required,
        "risk_level": args.risk_level,
        "test_cases": csv(args.test_cases),
        "eval_metrics": [],
        "sandbox_status": "not_run",
        "enabled": False,
        "deprecated_reason": None,
    }
    append_jsonl(skills_path, skill)
    audit("skill_candidate_created", f"skill={skill['skill_id']}", audit_path, skill_id=skill["skill_id"])
    print(json.dumps({"status": "created", "skill": skill, "note": "not installed and disabled"}, indent=2, ensure_ascii=False))


def skill_review(args, skills_path, reviews_path, audit_path):
    skill = find(load_jsonl(skills_path), "skill_id", args.skill_id)
    if skill is None:
        fail(f"skill '{args.skill_id}' not found", "not_found")
    review = {
        "skill_review_id": f"skillreview_{uuid4().hex[:12]}",
        "skill_ref": args.skill_id,
        "result": args.result,
        "notes": args.notes,
        "enabled_after_review": False,
        "created_at": now_iso(),
    }
    append_jsonl(reviews_path, review)
    audit("skill_review_created", f"review={review['skill_review_id']}", audit_path, skill_id=args.skill_id)
    print(json.dumps({"status": "created", "review": review}, indent=2, ensure_ascii=False))


def kg_node(args, nodes_path, audit_path):
    if not args.label.strip():
        fail("label required")
    if has_secret(args.label, args.summary):
        fail("secret-like content rejected", "rejected")
    node = {
        "node_id": f"knode_{uuid4().hex[:12]}",
        "node_type": args.node_type,
        "label": args.label.strip(),
        "summary": args.summary or None,
        "source_refs": csv(args.source_refs),
        "confidence": max(0.0, min(1.0, float(args.confidence))),
        "status": "candidate",
        "created_at": now_iso(),
    }
    append_jsonl(nodes_path, node)
    audit("knowledge_node_created", f"node={node['node_id']}", audit_path, node_id=node["node_id"])
    print(json.dumps({"status": "created", "node": node}, indent=2, ensure_ascii=False))


def kg_edge(args, nodes_path, edges_path, audit_path):
    nodes = load_jsonl(nodes_path)
    if find(nodes, "node_id", args.from_node_ref) is None or find(nodes, "node_id", args.to_node_ref) is None:
        fail("from_node_ref and to_node_ref must exist", "not_found")
    edge = {
        "edge_id": f"kedge_{uuid4().hex[:12]}",
        "from_node_ref": args.from_node_ref,
        "to_node_ref": args.to_node_ref,
        "relation": args.relation,
        "source_refs": csv(args.source_refs),
        "confidence": max(0.0, min(1.0, float(args.confidence))),
        "status": "candidate",
        "created_at": now_iso(),
    }
    append_jsonl(edges_path, edge)
    audit("knowledge_edge_created", f"edge={edge['edge_id']}", audit_path, edge_id=edge["edge_id"])
    print(json.dumps({"status": "created", "edge": edge}, indent=2, ensure_ascii=False))


def boundary_create(args, boundaries_path, audit_path):
    if not args.summary.strip():
        fail("summary required")
    boundary = {
        "boundary_id": f"boundary_{uuid4().hex[:12]}",
        "boundary_type": args.boundary_type,
        "summary": args.summary.strip(),
        "source_refs": csv(args.source_refs),
        "status": "candidate",
        "created_at": now_iso(),
    }
    append_jsonl(boundaries_path, boundary)
    audit("boundary_candidate_created", f"boundary={boundary['boundary_id']}", audit_path, boundary_id=boundary["boundary_id"])
    print(json.dumps({"status": "created", "boundary": boundary}, indent=2, ensure_ascii=False))


def kg_state(args, nodes_path, edges_path, boundaries_path, state_path, audit_path):
    state = {
        "knowledge_state_id": f"kstate_{uuid4().hex[:12]}",
        "node_count": len(load_jsonl(nodes_path)),
        "edge_count": len(load_jsonl(edges_path)),
        "boundary_count": len(load_jsonl(boundaries_path)),
        "rag_enabled": False,
        "created_at": now_iso(),
    }
    append_jsonl(state_path, state)
    audit("knowledge_state_created", f"state={state['knowledge_state_id']}", audit_path, knowledge_state_id=state["knowledge_state_id"])
    print(json.dumps({"status": "created", "knowledge_state": state, "note": "RAG disabled"}, indent=2, ensure_ascii=False))


def model_route(args, routes_path, audit_path):
    if not args.task_type.strip():
        fail("task_type required")
    route = {
        "router_id": f"modelroute_{uuid4().hex[:12]}",
        "task_type": args.task_type.strip(),
        "default_model": args.default_model,
        "fallback_model": args.fallback_model,
        "budget_class": args.budget_class,
        "litellm_enabled": False,
        "status": "draft",
        "created_at": now_iso(),
    }
    append_jsonl(routes_path, route)
    audit("model_route_created", f"route={route['router_id']}", audit_path, router_id=route["router_id"])
    print(json.dumps({"status": "created", "route": route, "note": "LiteLLM disabled"}, indent=2, ensure_ascii=False))


def cost_event(args, costs_path, audit_path):
    try:
        amount = float(args.estimated_cost_usd)
    except ValueError:
        fail("estimated_cost_usd must be numeric")
    event = {
        "cost_event_id": f"costevt_{uuid4().hex[:12]}",
        "task_ref": args.task_ref,
        "model": args.model,
        "estimated_cost_usd": max(0.0, amount),
        "budget_class": args.budget_class,
        "created_at": now_iso(),
    }
    append_jsonl(costs_path, event)
    audit("cost_event_created", f"cost={event['cost_event_id']}", audit_path, cost_event_id=event["cost_event_id"])
    print(json.dumps({"status": "created", "cost_event": event}, indent=2, ensure_ascii=False))


def mcp_profile(args, profiles_path, audit_path):
    if not args.name.strip():
        fail("name required")
    profile = {
        "mcp_profile_id": f"mcpprof_{uuid4().hex[:12]}",
        "name": args.name.strip(),
        "trust_level": args.trust_level,
        "enabled": False,
        "network_access": bool(args.network_access),
        "write_actions_allowed": False,
        "approval_required": True,
        "allowed_tools": csv(args.allowed_tools),
        "created_at": now_iso(),
    }
    append_jsonl(profiles_path, profile)
    audit("mcp_profile_created", f"profile={profile['mcp_profile_id']}", audit_path, mcp_profile_id=profile["mcp_profile_id"])
    print(json.dumps({"status": "created", "profile": profile, "note": "MCP remains disabled"}, indent=2, ensure_ascii=False))


def tool_policy(args, policies_path, audit_path):
    if not args.tool_ref.strip():
        fail("tool_ref required")
    policy = {
        "tool_trust_policy_id": f"tooltrust_{uuid4().hex[:12]}",
        "tool_ref": args.tool_ref.strip(),
        "trust_level": args.trust_level,
        "external_effect": bool(args.external_effect),
        "write_allowed": False,
        "approval_required": True,
        "status": "draft",
        "created_at": now_iso(),
    }
    append_jsonl(policies_path, policy)
    audit("tool_trust_policy_created", f"policy={policy['tool_trust_policy_id']}", audit_path, tool_trust_policy_id=policy["tool_trust_policy_id"])
    print(json.dumps({"status": "created", "policy": policy}, indent=2, ensure_ascii=False))


def list_records(args, paths):
    if args.record_type not in paths:
        fail("unknown record_type")
    rows = load_jsonl(paths[args.record_type])
    limit = min(args.limit or 20, 100)
    print(json.dumps({args.record_type: rows[-limit:], "total": len(rows), "shown": min(limit, len(rows))},
                     indent=2, ensure_ascii=False))


def add_paths(parser):
    parser.add_argument("--workflows-log", default=None)
    parser.add_argument("--runs-log", default=None)
    parser.add_argument("--skills-log", default=None)
    parser.add_argument("--skill-reviews-log", default=None)
    parser.add_argument("--nodes-log", default=None)
    parser.add_argument("--edges-log", default=None)
    parser.add_argument("--boundaries-log", default=None)
    parser.add_argument("--state-log", default=None)
    parser.add_argument("--model-routes-log", default=None)
    parser.add_argument("--cost-events-log", default=None)
    parser.add_argument("--mcp-profiles-log", default=None)
    parser.add_argument("--tool-policies-log", default=None)
    parser.add_argument("--audit-log", default=None)


def main():
    parser = argparse.ArgumentParser(description="OnePal Readiness Center")
    sub = parser.add_subparsers(dest="cmd")

    wf = sub.add_parser("workflow-create")
    wf.add_argument("--name", required=True)
    wf.add_argument("--owner-agent", default="Automation/Input Agent")
    wf.add_argument("--risk-level", default="R2")
    wf.add_argument("--trigger-type", default="manual", choices=["manual", "scheduled", "event", "webhook"])
    wf.add_argument("--schedule-ref", default=None)
    wf.add_argument("--action-refs", default="")
    add_paths(wf)

    wr = sub.add_parser("workflow-trigger")
    wr.add_argument("--workflow-id", required=True)
    wr.add_argument("--triggered-by", default="user")
    wr.add_argument("--input-refs", default="")
    add_paths(wr)

    sc = sub.add_parser("skill-candidate")
    sc.add_argument("--name", required=True)
    sc.add_argument("--description", default="")
    sc.add_argument("--owner-agent", default="Capability HR Agent")
    sc.add_argument("--trigger-conditions", default="")
    sc.add_argument("--input-schema-ref", default="none")
    sc.add_argument("--output-schema-ref", default="none")
    sc.add_argument("--required-actions", default="")
    sc.add_argument("--permission-required", default="local_write_with_approval")
    sc.add_argument("--risk-level", default="R2")
    sc.add_argument("--test-cases", default="")
    add_paths(sc)

    sr = sub.add_parser("skill-review")
    sr.add_argument("--skill-id", required=True)
    sr.add_argument("--result", default="passed", choices=["passed", "failed"])
    sr.add_argument("--notes", default="")
    add_paths(sr)

    kn = sub.add_parser("kg-node")
    kn.add_argument("--node-type", default="concept")
    kn.add_argument("--label", required=True)
    kn.add_argument("--summary", default="")
    kn.add_argument("--source-refs", default="")
    kn.add_argument("--confidence", type=float, default=0.7)
    add_paths(kn)

    ke = sub.add_parser("kg-edge")
    ke.add_argument("--from-node-ref", required=True)
    ke.add_argument("--to-node-ref", required=True)
    ke.add_argument("--relation", default="relates_to")
    ke.add_argument("--source-refs", default="")
    ke.add_argument("--confidence", type=float, default=0.7)
    add_paths(ke)

    bc = sub.add_parser("boundary-create")
    bc.add_argument("--boundary-type", default="open_question")
    bc.add_argument("--summary", required=True)
    bc.add_argument("--source-refs", default="")
    add_paths(bc)

    ks = sub.add_parser("kg-state")
    add_paths(ks)

    mr = sub.add_parser("model-route")
    mr.add_argument("--task-type", required=True)
    mr.add_argument("--default-model", default="local/manual")
    mr.add_argument("--fallback-model", default=None)
    mr.add_argument("--budget-class", default="medium")
    add_paths(mr)

    ce = sub.add_parser("cost-event")
    ce.add_argument("--task-ref", required=True)
    ce.add_argument("--model", default="local/manual")
    ce.add_argument("--estimated-cost-usd", default="0")
    ce.add_argument("--budget-class", default="low")
    add_paths(ce)

    mp = sub.add_parser("mcp-profile")
    mp.add_argument("--name", required=True)
    mp.add_argument("--trust-level", default="unverified")
    mp.add_argument("--network-access", action="store_true")
    mp.add_argument("--allowed-tools", default="")
    add_paths(mp)

    tp = sub.add_parser("tool-policy")
    tp.add_argument("--tool-ref", required=True)
    tp.add_argument("--trust-level", default="local_sandbox_tool")
    tp.add_argument("--external-effect", action="store_true")
    add_paths(tp)

    listing = sub.add_parser("list")
    listing.add_argument("--record-type", required=True)
    listing.add_argument("--limit", type=int, default=20)
    add_paths(listing)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    paths = {
        "workflows": Path(args.workflows_log) if getattr(args, "workflows_log", None) else DEFAULT_WORKFLOWS,
        "runs": Path(args.runs_log) if getattr(args, "runs_log", None) else DEFAULT_RUNS,
        "skills": Path(args.skills_log) if getattr(args, "skills_log", None) else DEFAULT_SKILLS,
        "skill_reviews": Path(args.skill_reviews_log) if getattr(args, "skill_reviews_log", None) else DEFAULT_SKILL_REVIEWS,
        "nodes": Path(args.nodes_log) if getattr(args, "nodes_log", None) else DEFAULT_NODES,
        "edges": Path(args.edges_log) if getattr(args, "edges_log", None) else DEFAULT_EDGES,
        "boundaries": Path(args.boundaries_log) if getattr(args, "boundaries_log", None) else DEFAULT_BOUNDARIES,
        "knowledge_state": Path(args.state_log) if getattr(args, "state_log", None) else DEFAULT_KSTATE,
        "model_routes": Path(args.model_routes_log) if getattr(args, "model_routes_log", None) else DEFAULT_MODEL_ROUTES,
        "cost_events": Path(args.cost_events_log) if getattr(args, "cost_events_log", None) else DEFAULT_COST_EVENTS,
        "mcp_profiles": Path(args.mcp_profiles_log) if getattr(args, "mcp_profiles_log", None) else DEFAULT_MCP_PROFILES,
        "tool_policies": Path(args.tool_policies_log) if getattr(args, "tool_policies_log", None) else DEFAULT_TOOL_POLICIES,
    }
    audit_path = Path(args.audit_log) if getattr(args, "audit_log", None) else DEFAULT_AUDIT

    if args.cmd == "workflow-create":
        workflow_create(args, paths["workflows"], audit_path)
    elif args.cmd == "workflow-trigger":
        workflow_trigger(args, paths["workflows"], paths["runs"], audit_path)
    elif args.cmd == "skill-candidate":
        skill_candidate(args, paths["skills"], audit_path)
    elif args.cmd == "skill-review":
        skill_review(args, paths["skills"], paths["skill_reviews"], audit_path)
    elif args.cmd == "kg-node":
        kg_node(args, paths["nodes"], audit_path)
    elif args.cmd == "kg-edge":
        kg_edge(args, paths["nodes"], paths["edges"], audit_path)
    elif args.cmd == "boundary-create":
        boundary_create(args, paths["boundaries"], audit_path)
    elif args.cmd == "kg-state":
        kg_state(args, paths["nodes"], paths["edges"], paths["boundaries"], paths["knowledge_state"], audit_path)
    elif args.cmd == "model-route":
        model_route(args, paths["model_routes"], audit_path)
    elif args.cmd == "cost-event":
        cost_event(args, paths["cost_events"], audit_path)
    elif args.cmd == "mcp-profile":
        mcp_profile(args, paths["mcp_profiles"], audit_path)
    elif args.cmd == "tool-policy":
        tool_policy(args, paths["tool_policies"], audit_path)
    elif args.cmd == "list":
        list_records(args, paths)


if __name__ == "__main__":
    main()
