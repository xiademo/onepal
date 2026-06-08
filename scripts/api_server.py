#!/usr/bin/env python3
"""OnePal Minimum API Server - Task 06

Local HTTP API control plane. Binds to 127.0.0.1 only.
Provides read-only access to health, tasks, task-trees, task-runs, mas-trace,
and a POST /command endpoint that delegates to command_gateway.py.

Does NOT: execute actions, bypass governance, read secrets, expose files.

Usage:
    py scripts/api_server.py --host 127.0.0.1 --port 18790
"""

import argparse
import json
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = "py"

# Allowed read paths (whitelist — no arbitrary file access)
HEALTH_PATH = PROJECT_ROOT / "runtime" / "health_status.json"
TASKS_PATH = PROJECT_ROOT / "runtime" / "tasks" / "tasks.jsonl"
TREES_PATH = PROJECT_ROOT / "runtime" / "tasks" / "task_trees.jsonl"
TASK_RUNS_PATH = PROJECT_ROOT / "runtime" / "task_runs" / "task_runs.jsonl"
MAS_TRACE_PATH = PROJECT_ROOT / "logs" / "mas_trace.jsonl"
COMMAND_GATEWAY = PROJECT_ROOT / "scripts" / "command_gateway.py"
MEMORY_CANDIDATE_SCRIPT = PROJECT_ROOT / "scripts" / "memory_candidate.py"
MEMORY_STORE_SCRIPT = PROJECT_ROOT / "scripts" / "memory_store.py"
MEMORY_GOVERNANCE_SCRIPT = PROJECT_ROOT / "scripts" / "memory_governance.py"
MEMORY_CANDIDATES_PATH = PROJECT_ROOT / "memory" / "candidates" / "memory_candidates.jsonl"
MEMORY_PROPOSALS_PATH = PROJECT_ROOT / "memory" / "proposals" / "memory_proposals.jsonl"
MEMORY_STORE_PATH = PROJECT_ROOT / "memory" / "store" / "memory_store.jsonl"
MEMORY_REVIEWS_PATH = PROJECT_ROOT / "memory" / "reviews" / "memory_quality_reviews.jsonl"
MEMORY_CONFLICTS_PATH = PROJECT_ROOT / "memory" / "conflicts" / "memory_conflicts.jsonl"
MEMORY_CHANGES_PATH = PROJECT_ROOT / "memory" / "changes" / "memory_change_requests.jsonl"
MEMORY_SNAPSHOTS_PATH = PROJECT_ROOT / "memory" / "snapshots" / "memory_snapshots.jsonl"
MEMORY_SNAPSHOT_DIR = PROJECT_ROOT / "memory" / "snapshots" / "files"
RESEARCH_SOURCES_PATH = PROJECT_ROOT / "research" / "sources" / "research_sources.jsonl"
RESEARCH_PACKETS_PATH = PROJECT_ROOT / "research" / "packets" / "research_packets.jsonl"
RESEARCH_EVIDENCE_PATH = PROJECT_ROOT / "research" / "evidence" / "evidence_packs.jsonl"
RESEARCH_CARDS_PATH = PROJECT_ROOT / "research" / "cognition" / "cognition_cards.jsonl"
RESEARCH_HANDOFFS_DIR = PROJECT_ROOT / "research" / "handoffs"
RESEARCH_PACKET_SCRIPT = PROJECT_ROOT / "scripts" / "research_packet.py"
COGNITION_CARD_SCRIPT = PROJECT_ROOT / "scripts" / "cognition_card.py"
GROWTH_GOAL_SCRIPT = PROJECT_ROOT / "scripts" / "growth_goal.py"
GROWTH_PLAN_SCRIPT = PROJECT_ROOT / "scripts" / "growth_plan.py"
GROWTH_REVIEW_SCRIPT = PROJECT_ROOT / "scripts" / "growth_review.py"
GROWTH_CANDIDATES_PATH = PROJECT_ROOT / "growth" / "candidates" / "goal_candidates.jsonl"
GROWTH_GOALS_PATH = PROJECT_ROOT / "growth" / "goals" / "goal_contracts.jsonl"
GROWTH_CAPACITY_PATH = PROJECT_ROOT / "growth" / "capacity" / "capacity_budgets.jsonl"
GROWTH_WEEKLY_PATH = PROJECT_ROOT / "growth" / "plans" / "weekly_plans.jsonl"
GROWTH_TASKS_PATH = PROJECT_ROOT / "growth" / "plans" / "daily_tasks.jsonl"
GROWTH_REVIEWS_PATH = PROJECT_ROOT / "growth" / "reviews" / "growth_reviews.jsonl"
GROWTH_ADJUSTMENTS_PATH = PROJECT_ROOT / "growth" / "adjustments" / "plan_adjustment_proposals.jsonl"
GROWTH_HANDOFFS_PATH = PROJECT_ROOT / "growth" / "handoffs" / "growth_handoffs.jsonl"
GROWTH_AUDIT_PATH = PROJECT_ROOT / "logs" / "growth_audit.jsonl"
CAREER_CENTER_SCRIPT = PROJECT_ROOT / "scripts" / "career_center.py"
CAREER_ASSETS_PATH = PROJECT_ROOT / "career" / "assets" / "career_assets.jsonl"
CAREER_CLAIMS_PATH = PROJECT_ROOT / "career" / "claims" / "resume_claims.jsonl"
CAREER_JDS_PATH = PROJECT_ROOT / "career" / "jds" / "jd_items.jsonl"
CAREER_EVALUATIONS_PATH = PROJECT_ROOT / "career" / "evaluations" / "jd_evaluations.jsonl"
CAREER_APPLICATIONS_PATH = PROJECT_ROOT / "career" / "applications" / "application_records.jsonl"
CAREER_HANDOFFS_PATH = PROJECT_ROOT / "career" / "handoffs" / "career_handoffs.jsonl"
CAREER_AUDIT_PATH = PROJECT_ROOT / "logs" / "career_audit.jsonl"
READINESS_CENTER_SCRIPT = PROJECT_ROOT / "scripts" / "readiness_center.py"
AUTOMATION_WORKFLOWS_PATH = PROJECT_ROOT / "automation" / "workflows" / "automation_workflows.jsonl"
AUTOMATION_RUNS_PATH = PROJECT_ROOT / "automation" / "runs" / "workflow_runs.jsonl"
SKILL_CANDIDATES_PATH = PROJECT_ROOT / "capabilities" / "skills" / "skill_candidates.jsonl"
SKILL_REVIEWS_PATH = PROJECT_ROOT / "capabilities" / "skills" / "skill_reviews.jsonl"
KNOWLEDGE_NODES_PATH = PROJECT_ROOT / "knowledge_graph" / "nodes.jsonl"
KNOWLEDGE_EDGES_PATH = PROJECT_ROOT / "knowledge_graph" / "edges.jsonl"
KNOWLEDGE_BOUNDARIES_PATH = PROJECT_ROOT / "knowledge_graph" / "boundaries.jsonl"
KNOWLEDGE_STATE_PATH = PROJECT_ROOT / "knowledge_graph" / "state.jsonl"
MODEL_ROUTES_PATH = PROJECT_ROOT / "model_cost" / "model_routes.jsonl"
COST_EVENTS_PATH = PROJECT_ROOT / "model_cost" / "cost_events.jsonl"
MCP_PROFILES_PATH = PROJECT_ROOT / "mcp" / "profiles" / "mcp_server_profiles.jsonl"
TOOL_POLICIES_PATH = PROJECT_ROOT / "mcp" / "policies" / "tool_trust_policies.jsonl"
READINESS_AUDIT_PATH = PROJECT_ROOT / "logs" / "readiness_audit.jsonl"

MAX_LIMIT = 100
MAX_COMMAND_LENGTH = 2000
MAX_MEMORY_CONTENT = 4000
MAX_GROWTH_CONTENT = 2000

ALLOWED_HOSTS = {"127.0.0.1", "localhost"}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path, limit=20):
    """Read latest N JSON lines from a JSONL file. Returns list, skipped_count."""
    results = []
    skipped = 0
    limit = min(int(limit), MAX_LIMIT)

    if not path.exists():
        return [], 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return [], 0

    # Take latest N lines
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            skipped += 1

    return results, skipped


def build_response(ok, data=None, error=None, meta_extra=None):
    """Unified JSON response format."""
    meta = {"timestamp": now_iso()}
    if meta_extra:
        meta.update(meta_extra)
    return {
        "ok": ok,
        "data": data if data is not None else {},
        "error": error,
        "meta": meta,
    }


def handle_health(health_path):
    """GET /health handler."""
    if health_path.exists():
        try:
            with open(health_path, "r", encoding="utf-8") as f:
                health_data = json.load(f)
            return build_response(True, data={
                "status": health_data.get("status", "unknown"),
                "source": "runtime/health_status.json",
                "exists": True,
                "last_updated": health_data.get("checked_at"),
            })
        except (json.JSONDecodeError, OSError):
            return build_response(True, data={
                "status": "limited",
                "source": "runtime/health_status.json",
                "exists": True,
                "note": "file exists but could not be parsed",
            })
    else:
        return build_response(True, data={
            "status": "limited",
            "source": "none",
            "exists": False,
            "note": "health_status.json not found",
        })


def handle_tasks(tasks_path, limit):
    """GET /tasks handler."""
    results, skipped = read_jsonl(tasks_path, limit)
    return build_response(True, data={"tasks": results}, meta_extra={
        "total": len(results),
        "skipped": skipped,
        "limit": limit,
        "source": "runtime/tasks/tasks.jsonl",
    })


def handle_task_trees(trees_path, limit):
    """GET /task-trees handler."""
    results, skipped = read_jsonl(trees_path, limit)
    return build_response(True, data={"task_trees": results}, meta_extra={
        "total": len(results),
        "skipped": skipped,
        "limit": limit,
        "source": "runtime/tasks/task_trees.jsonl",
    })


def _safe_source(path, default="file"):
    """Return a safe source string for a path, or default if outside project."""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return default


def handle_task_runs(path, limit):
    """GET /task-runs handler."""
    results, skipped = read_jsonl(path, limit)
    source = _safe_source(path, "none") if path.exists() else "none"
    return build_response(True, data={"task_runs": results}, meta_extra={
        "total": len(results),
        "skipped": skipped,
        "limit": limit,
        "source": source,
    })


def handle_mas_trace(path, limit):
    """GET /mas-trace handler."""
    results, skipped = read_jsonl(path, limit)
    return build_response(True, data={"mas_trace": results}, meta_extra={
        "total": len(results),
        "skipped": skipped,
        "limit": limit,
        "source": "logs/mas_trace.jsonl",
    })


def handle_command(body, gateway_path):
    """POST /command handler. Delegates to command_gateway.py via subprocess."""
    command_text = (body or "").strip()

    if not command_text:
        return build_response(False, error={
            "code": "EMPTY_COMMAND",
            "message": "command must not be empty",
        })

    if len(command_text) > MAX_COMMAND_LENGTH:
        return build_response(False, error={
            "code": "COMMAND_TOO_LONG",
            "message": f"command must be <= {MAX_COMMAND_LENGTH} characters",
        })

    # Subprocess delegation — no shell=True
    try:
        result = subprocess.run(
            ["py", str(gateway_path), "--command", command_text],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return build_response(False, error={
            "code": "GATEWAY_TIMEOUT",
            "message": "command_gateway.py timed out",
        })

    try:
        gateway_output = json.loads(result.stdout.strip()) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        gateway_output = {"raw_stdout": (result.stdout or "")[:500]}

    return build_response(True, data={
        "gateway_result": gateway_output,
        "gateway_exit_code": result.returncode,
    })


# ─── Memory API handlers ───

def _redact(content):
    """Return redacted version if content matches secret patterns."""
    import re as _re
    patterns = [r'sk-[a-zA-Z0-9]{10,}', r'-----BEGIN', r'ghp_[a-zA-Z0-9]{20,}',
                r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}',
                r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
                r'(?:api[_-]?key)\s*[:=]\s*\S{10,}', r'(?:password)\s*[:=]\s*\S{8,}',
                r'(?:token)\s*[:=]\s*\S{10,}', r'(?:secret)\s*[:=]\s*\S{8,}']
    for pat in patterns:
        if _re.search(pat, content or "", _re.IGNORECASE):
            return True, "[REDACTED]"
    return False, content


def _run_memory_cmd(cmd_args, timeout=30):
    """Run a memory script subprocess safely."""
    try:
        result = subprocess.run(
            [PY] + cmd_args,
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        out = (result.stdout or "").strip()
        try:
            data = json.loads(out) if out else {}
        except json.JSONDecodeError:
            data = {"raw_stdout": out[:500]}
        return True, data, result.returncode
    except subprocess.TimeoutExpired:
        return False, {"error": "timeout"}, -1
    except Exception as e:
        return False, {"error": str(e)[:200]}, -1


def _read_fixed_jsonl(path, limit=20):
    """Read latest N lines from a fixed JSONL path."""
    results, skipped = read_jsonl(path, limit)
    return results, skipped


def handle_memory_get(args, candidates_path, proposals_path, store_path, limit):
    """GET /memory handler."""
    results, skipped = read_jsonl(store_path, limit)
    status_filter = args.get("status", "active")
    mem_type = args.get("type")
    filtered = [m for m in results if m.get("status") == status_filter]
    if mem_type:
        filtered = [m for m in filtered if m.get("memory_type") == mem_type]
    # Redact secrets in content
    for m in filtered:
        is_redacted, redacted = _redact(m.get("content", ""))
        if is_redacted:
            m["content"] = "[REDACTED]"
            m["redacted"] = True
    return build_response(True, data={"memories": filtered[-limit:]}, meta_extra={
        "total": len(filtered), "limit": limit, "source": "memory/store/memory_store.jsonl"
    })


def handle_memory_candidates_get(path, limit, status=None):
    """GET /memory/candidates handler."""
    results, skipped = read_jsonl(path, limit)
    if status:
        results = [c for c in results if c.get("status") == status]
    # Redact secrets, return summaries only
    safe = []
    for c in results:
        entry = {
            "candidate_id": c.get("candidate_id"),
            "memory_type": c.get("memory_type"),
            "content_summary": (c.get("content") or c.get("content_summary") or "")[:200],
            "status": c.get("status"),
            "sensitivity": c.get("sensitivity"),
            "requires_user_confirmation": c.get("requires_user_confirmation"),
            "created_at": c.get("created_at"),
        }
        is_redacted, _ = _redact(c.get("content", ""))
        if is_redacted:
            entry["content_summary"] = "[REDACTED]"
            entry["redacted"] = True
        safe.append(entry)
    return build_response(True, data={"candidates": safe[-limit:]}, meta_extra={
        "total": len(safe), "skipped": skipped, "limit": limit
    })


def handle_memory_proposals_get(path, limit):
    """GET /memory/proposals handler."""
    results, skipped = read_jsonl(path, limit)
    safe = [{
        "proposal_id": p.get("proposal_id"),
        "candidate_id": p.get("candidate_id"),
        "proposal_type": p.get("proposal_type"),
        "memory_type": p.get("memory_type"),
        "status": p.get("status"),
        "risk_level": p.get("sensitivity", "?") if isinstance(p.get("sensitivity"), str) else "?",
        "requires_approval": p.get("requires_approval", True),
        "created_at": p.get("created_at"),
    } for p in results]
    return build_response(True, data={"proposals": safe[-limit:]}, meta_extra={
        "total": len(safe), "limit": limit
    })


def handle_memory_candidates_post(body, script_path):
    """POST /memory/candidates handler."""
    content = (body.get("content") or body.get("content_summary") or "").strip()
    if not content:
        return build_response(False, error={"code": "EMPTY_CONTENT", "message": "content must not be empty"})
    if len(content) > MAX_MEMORY_CONTENT:
        return build_response(False, error={"code": "CONTENT_TOO_LONG", "message": f"content must be <= {MAX_MEMORY_CONTENT} chars"})

    ok, data, ec = _run_memory_cmd([
        str(script_path), "create",
        "--content", content,
        "--memory-type", body.get("memory_type", "project_decision"),
        "--source-type", body.get("source_type", "manual"),
        "--source-agent", body.get("source_agent", "user"),
        "--sensitivity", body.get("sensitivity", "personal"),
        "--confidence", str(body.get("confidence", 0.8)),
    ])
    if not ok:
        return build_response(False, error={"code": "SCRIPT_ERROR", "message": data.get("error", "unknown")})
    if data.get("status") == "rejected":
        return build_response(False, error={"code": "CANDIDATE_REJECTED", "message": data.get("reason", "rejected")})
    return build_response(True, data={"candidate_id": data.get("candidate", {}).get("candidate_id"), "status": data.get("status")})


def handle_memory_proposals_post(body, script_path):
    """POST /memory/proposals handler."""
    cid = (body.get("candidate_id") or "").strip()
    if not cid:
        return build_response(False, error={"code": "MISSING_ID", "message": "candidate_id required"})
    reason = body.get("reason", "")
    args = [str(script_path), "propose", "--candidate-id", cid]
    if reason:
        args.extend(["--reason", reason])
    ok, data, ec = _run_memory_cmd(args)
    if not ok:
        return build_response(False, error={"code": "SCRIPT_ERROR", "message": data.get("error", "unknown")})
    if data.get("status") == "rejected":
        return build_response(False, error={"code": "PROPOSAL_REJECTED", "message": data.get("reason", "rejected")})
    if data.get("status") == "deduped":
        return build_response(True, data={"status": "deduped", "existing_candidate_id": data.get("existing_candidate_id"), "message": "duplicate exists"})
    return build_response(True, data={"proposal_id": data.get("proposal", {}).get("proposal_id"), "status": data.get("status")})


def handle_memory_store_post(body, script_path):
    """POST /memory/store handler."""
    pid = (body.get("proposal_id") or "").strip()
    if not pid:
        return build_response(False, error={"code": "MISSING_ID", "message": "proposal_id required"})
    ok, data, ec = _run_memory_cmd([str(script_path), "store", "--proposal-id", pid])
    if not ok:
        return build_response(False, error={"code": "SCRIPT_ERROR", "message": data.get("error", "unknown")})
    if data.get("status") == "rejected":
        return build_response(False, error={"code": "STORE_REJECTED", "message": data.get("reason", data.get("error", "rejected"))})
    return build_response(True, data={"memory_id": data.get("memory", {}).get("memory_id"), "status": data.get("status")})


def handle_memory_archive_post(body, script_path):
    """POST /memory/archive handler."""
    mid = (body.get("memory_id") or "").strip()
    if not mid:
        return build_response(False, error={"code": "MISSING_ID", "message": "memory_id required"})
    reason = body.get("reason", "api_archive")
    ok, data, ec = _run_memory_cmd([str(script_path), "archive", "--memory-id", mid, "--reason", reason])
    if not ok:
        return build_response(False, error={"code": "SCRIPT_ERROR", "message": data.get("error", "unknown")})
    return build_response(True, data={"memory_id": mid, "status": data.get("status", "archived")})


def _memory_governance_get(path, key, limit):
    results, skipped = read_jsonl(path, limit)
    return build_response(True, data={key: results[-limit:]}, meta_extra={
        "total": len(results),
        "skipped": skipped,
        "limit": limit,
        "source": _safe_source(path, "none") if path.exists() else "none",
    })


def handle_memory_reviews_get(path, limit):
    return _memory_governance_get(path, "reviews", limit)


def handle_memory_conflicts_get(path, limit):
    return _memory_governance_get(path, "conflicts", limit)


def handle_memory_changes_get(path, limit):
    return _memory_governance_get(path, "changes", limit)


def handle_memory_snapshots_get(path, limit):
    return _memory_governance_get(path, "snapshots", limit)


def _memory_governance_paths(candidates_path, store_path, reviews_path, conflicts_path,
                             changes_path, snapshots_path, snapshot_dir, audit_path):
    return [
        "--candidates-log", str(candidates_path),
        "--store-log", str(store_path),
        "--reviews-log", str(reviews_path),
        "--conflicts-log", str(conflicts_path),
        "--changes-log", str(changes_path),
        "--snapshots-log", str(snapshots_path),
        "--snapshot-dir", str(snapshot_dir),
        "--audit-log", str(audit_path),
    ]


def handle_memory_review_post(body, script_path, candidates_path=MEMORY_CANDIDATES_PATH,
                              store_path=MEMORY_STORE_PATH, reviews_path=MEMORY_REVIEWS_PATH,
                              conflicts_path=MEMORY_CONFLICTS_PATH, changes_path=MEMORY_CHANGES_PATH,
                              snapshots_path=MEMORY_SNAPSHOTS_PATH, snapshot_dir=MEMORY_SNAPSHOT_DIR,
                              audit_path=PROJECT_ROOT / "logs" / "memory_audit.jsonl"):
    target_type = (body.get("target_type") or "").strip()
    target_ref = (body.get("target_ref") or "").strip()
    if target_type not in ("candidate", "entry"):
        return build_response(False, error={"code": "INVALID_TYPE", "message": "target_type must be candidate or entry"})
    if not target_ref:
        return build_response(False, error={"code": "MISSING_ID", "message": "target_ref required"})
    args = [str(script_path), "review-create", "--target-type", target_type, "--target-ref", target_ref]
    notes = (body.get("review_notes") or "").strip()
    if _redact(notes)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    if notes:
        args.extend(["--review-notes", notes])
    args.extend(_memory_governance_paths(candidates_path, store_path, reviews_path, conflicts_path,
                                         changes_path, snapshots_path, snapshot_dir, audit_path))
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return build_response(False, error={"code": "SCRIPT_ERROR", "message": data.get("error", "memory governance script failed")})
    return build_response(True, data={"review_id": data.get("review", {}).get("memory_quality_review_id"),
                                      "status": data.get("status"),
                                      "recommendation": data.get("review", {}).get("recommendation")})


def handle_memory_conflict_post(body, script_path, candidates_path=MEMORY_CANDIDATES_PATH,
                                store_path=MEMORY_STORE_PATH, reviews_path=MEMORY_REVIEWS_PATH,
                                conflicts_path=MEMORY_CONFLICTS_PATH, changes_path=MEMORY_CHANGES_PATH,
                                snapshots_path=MEMORY_SNAPSHOTS_PATH, snapshot_dir=MEMORY_SNAPSHOT_DIR,
                                audit_path=PROJECT_ROOT / "logs" / "memory_audit.jsonl"):
    target_type = (body.get("target_type") or "").strip()
    target_ref = (body.get("target_ref") or "").strip()
    if target_type not in ("candidate", "entry"):
        return build_response(False, error={"code": "INVALID_TYPE", "message": "target_type must be candidate or entry"})
    if not target_ref:
        return build_response(False, error={"code": "MISSING_ID", "message": "target_ref required"})
    args = [str(script_path), "conflict-detect", "--target-type", target_type, "--target-ref", target_ref]
    args.extend(_memory_governance_paths(candidates_path, store_path, reviews_path, conflicts_path,
                                         changes_path, snapshots_path, snapshot_dir, audit_path))
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return build_response(False, error={"code": "SCRIPT_ERROR", "message": data.get("error", "memory governance script failed")})
    conflict = data.get("conflict", {})
    return build_response(True, data={"conflict_id": conflict.get("memory_conflict_id"),
                                      "status": data.get("status"),
                                      "conflicts": data.get("conflicts", [])})


def handle_memory_change_post(body, script_path, candidates_path=MEMORY_CANDIDATES_PATH,
                              store_path=MEMORY_STORE_PATH, reviews_path=MEMORY_REVIEWS_PATH,
                              conflicts_path=MEMORY_CONFLICTS_PATH, changes_path=MEMORY_CHANGES_PATH,
                              snapshots_path=MEMORY_SNAPSHOTS_PATH, snapshot_dir=MEMORY_SNAPSHOT_DIR,
                              audit_path=PROJECT_ROOT / "logs" / "memory_audit.jsonl"):
    change_type = (body.get("change_type") or "").strip()
    target_refs = _csv(body.get("target_refs", ""))
    reason = (body.get("reason") or "").strip()
    if not change_type:
        return build_response(False, error={"code": "MISSING_TYPE", "message": "change_type required"})
    if not target_refs:
        return build_response(False, error={"code": "MISSING_ID", "message": "target_refs required"})
    if not reason:
        return build_response(False, error={"code": "EMPTY_REASON", "message": "reason required"})
    if _redact(reason)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    args = [str(script_path), "change-create", "--change-type", change_type,
            "--target-refs", target_refs, "--reason", reason]
    if body.get("source_candidate_id"):
        args.extend(["--source-candidate-id", str(body.get("source_candidate_id"))])
    if body.get("source_memory_id"):
        args.extend(["--source-memory-id", str(body.get("source_memory_id"))])
    if body.get("snapshot_ref"):
        args.extend(["--snapshot-ref", str(body.get("snapshot_ref"))])
    args.extend(_memory_governance_paths(candidates_path, store_path, reviews_path, conflicts_path,
                                         changes_path, snapshots_path, snapshot_dir, audit_path))
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return build_response(False, error={"code": "SCRIPT_ERROR", "message": data.get("error", "memory governance script failed")})
    change = data.get("change_request", {})
    return build_response(True, data={"change_request_id": change.get("memory_change_request_id"),
                                      "status": data.get("status"),
                                      "requires_user_approval": change.get("requires_user_approval", True)})


def handle_memory_snapshot_post(body, script_path, candidates_path=MEMORY_CANDIDATES_PATH,
                                store_path=MEMORY_STORE_PATH, reviews_path=MEMORY_REVIEWS_PATH,
                                conflicts_path=MEMORY_CONFLICTS_PATH, changes_path=MEMORY_CHANGES_PATH,
                                snapshots_path=MEMORY_SNAPSHOTS_PATH, snapshot_dir=MEMORY_SNAPSHOT_DIR,
                                audit_path=PROJECT_ROOT / "logs" / "memory_audit.jsonl"):
    reason = (body.get("reason") or "").strip()
    if not reason:
        return build_response(False, error={"code": "EMPTY_REASON", "message": "reason required"})
    if _redact(reason)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    args = [str(script_path), "snapshot-create", "--reason", reason]
    args.extend(_memory_governance_paths(candidates_path, store_path, reviews_path, conflicts_path,
                                         changes_path, snapshots_path, snapshot_dir, audit_path))
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return build_response(False, error={"code": "SCRIPT_ERROR", "message": data.get("error", "memory governance script failed")})
    snapshot = data.get("snapshot", {})
    return build_response(True, data={"snapshot_id": snapshot.get("memory_snapshot_id"),
                                      "status": data.get("status"),
                                      "entry_count": snapshot.get("entry_count")})


# ─── Research API handlers ───

def handle_research_sources_get(path, limit):
    results, skipped = read_jsonl(path, limit)
    safe = [{"source_id": s.get("source_id"), "source_type": s.get("source_type"), "title": s.get("title"),
             "source_level": s.get("source_level","?"), "credibility_score": s.get("credibility_score"),
             "freshness": s.get("freshness","?"), "status": s.get("status","?"),
             "created_at": s.get("created_at")} for s in results]
    for s in safe:
        is_r, _ = _redact(s.get("title",""))
        if is_r:
            s["title"] = "[REDACTED]"
            s["redacted"] = True
    return build_response(True, data={"sources": safe[-limit:]}, meta_extra={"total": len(safe), "limit": limit})

def handle_research_packets_get(path, limit):
    results, _ = read_jsonl(path, limit)
    safe = [{"packet_id": p.get("packet_id"), "topic": p.get("topic"), "question": p.get("question",""),
             "source_ids": p.get("source_ids",[]), "summary": p.get("summary",""),
             "key_findings": p.get("key_findings",[]), "uncertainties": p.get("uncertainties",[]),
             "recommended_next_action": p.get("recommended_next_action",""), "status": p.get("status"),
             "created_at": p.get("created_at")} for p in results]
    return build_response(True, data={"packets": safe[-limit:]}, meta_extra={"total": len(safe), "limit": limit})

def handle_research_evidence_get(path, limit):
    results, _ = read_jsonl(path, limit)
    safe = [{"evidence_pack_id": e.get("evidence_pack_id"), "packet_id": e.get("packet_id"),
             "confidence": e.get("confidence"), "claims": e.get("claims",[]), "created_at": e.get("created_at")} for e in results]
    return build_response(True, data={"evidence": safe[-limit:]}, meta_extra={"total": len(safe), "limit": limit})

def handle_research_cards_get(path, limit):
    results, _ = read_jsonl(path, limit)
    safe = [{"card_id": c.get("card_id"), "source_packet_id": c.get("source_packet_id"),
             "topic": c.get("topic"), "core_idea": c.get("core_idea",""), "why_it_matters": c.get("why_it_matters",""),
             "mental_model": c.get("mental_model",""), "self_test_questions": c.get("self_test_questions",[]),
             "confidence": c.get("confidence"), "status": c.get("status"), "created_at": c.get("created_at")} for c in results]
    return build_response(True, data={"cards": safe[-limit:]}, meta_extra={"total": len(safe), "limit": limit})

def handle_research_handoffs_get(limit):
    results = []
    if RESEARCH_HANDOFFS_DIR.exists():
        for f in RESEARCH_HANDOFFS_DIR.glob("*.jsonl"):
            recs, _ = read_jsonl(f, limit); results.extend(recs)
    safe = [{"handoff_id": h.get("handoff_id"), "handoff_type": h.get("handoff_type"),
             "source_type": h.get("source_type",""), "source_id": h.get("source_id",""),
             "summary": h.get("summary",""), "status": h.get("status"), "created_at": h.get("created_at")} for h in results]
    return build_response(True, data={"handoffs": safe[-limit:]}, meta_extra={"total": len(safe), "limit": limit})

def handle_research_sources_post(body, script_path):
    content = (body.get("content_summary") or "").strip()
    if not content: return build_response(False, error={"code":"EMPTY_CONTENT","message":"content required"})
    if len(content) > 2000: return build_response(False, error={"code":"CONTENT_TOO_LONG","message":"max 2000 chars"})
    ok, data, ec = _run_memory_cmd([str(script_path), "source-create", "--title", body.get("title","Untitled"),
                                     "--content-summary", content, "--source-type", body.get("source_type","manual_text"),
                                     "--source-level", body.get("source_level","unknown")])
    if not ok: return build_response(False, error={"code":"SCRIPT_ERROR","message":data.get("error","unknown")})
    return build_response(True, data={"source_id": data.get("source",{}).get("source_id"), "status": data.get("status")})

def handle_research_evaluate_post(body, script_path):
    sid = (body.get("source_id") or "").strip()
    if not sid: return build_response(False, error={"code":"MISSING_ID","message":"source_id required"})
    ok, data, _ = _run_memory_cmd([str(script_path), "source-evaluate", "--source-id", sid, "--trust-level", body.get("trust_level","B"),
                                    "--credibility-score", str(body.get("credibility_score",0.5)),
                                    "--freshness", body.get("freshness","acceptable")])
    if not ok: return build_response(False, error={"code":"SCRIPT_ERROR","message":data.get("error","unknown")})
    return build_response(True, data={"source_id": sid, "status": data.get("status","evaluated")})

def handle_research_packets_post(body, script_path):
    topic = (body.get("topic") or "").strip()
    src_ids = body.get("source_ids","")
    if not topic: return build_response(False, error={"code":"EMPTY_TOPIC","message":"topic required"})
    if not src_ids: return build_response(False, error={"code":"MISSING_SOURCES","message":"source_ids required"})
    ok, data, _ = _run_memory_cmd([str(script_path), "packet-create", "--topic", topic, "--question", body.get("question",""), "--source-ids", str(src_ids)])
    if not ok: return build_response(False, error={"code":"SCRIPT_ERROR","message":data.get("error","unknown")})
    return build_response(True, data={"packet_id": data.get("packet",{}).get("packet_id"), "status": data.get("status")})

def handle_research_evidence_post(body, script_path):
    pid = (body.get("packet_id") or "").strip()
    if not pid: return build_response(False, error={"code":"MISSING_ID","message":"packet_id required"})
    ok, data, _ = _run_memory_cmd([str(script_path), "evidence-create", "--packet-id", pid,
                                    "--claim-text", body.get("claim_text","Evidence claim"),
                                    "--claim-type", body.get("claim_type","fact"),
                                    "--confidence", str(body.get("confidence",0.5))])
    if not ok: return build_response(False, error={"code":"SCRIPT_ERROR","message":data.get("error","unknown")})
    return build_response(True, data={"evidence_pack_id": data.get("evidence",{}).get("evidence_pack_id"), "status": data.get("status")})

def handle_research_synthesize_post(body, script_path):
    pid = (body.get("packet_id") or "").strip()
    if not pid: return build_response(False, error={"code":"MISSING_ID","message":"packet_id required"})
    ok, data, _ = _run_memory_cmd([str(script_path), "packet-synthesize", "--packet-id", pid,
                                    "--summary", body.get("summary","Synthesized findings")])
    if not ok: return build_response(False, error={"code":"SCRIPT_ERROR","message":data.get("error","unknown")})
    return build_response(True, data={"packet_id": pid, "status": data.get("status","synthesized")})

def handle_research_cards_post(body, script_path):
    pid = (body.get("packet_id") or "").strip()
    if not pid: return build_response(False, error={"code":"MISSING_ID","message":"packet_id required"})
    ok, data, _ = _run_memory_cmd([str(script_path), "create", "--packet-id", pid,
                                    "--core-idea", body.get("core_idea",""),
                                    "--why-it-matters", body.get("why_it_matters",""),
                                    "--mental-model", body.get("mental_model",""),
                                    "--confidence", str(body.get("confidence",0.5))])
    if not ok: return build_response(False, error={"code":"SCRIPT_ERROR","message":data.get("error","unknown")})
    return build_response(True, data={"card_id": data.get("card",{}).get("card_id"), "status": data.get("status")})

def handle_research_handoffs_post(body, script_path):
    htype = (body.get("handoff_type") or "").strip()
    src_id = (body.get("source_id") or "").strip()
    if not htype: return build_response(False, error={"code":"MISSING_TYPE","message":"handoff_type required"})
    if not src_id: return build_response(False, error={"code":"MISSING_ID","message":"source_id required"})
    if htype not in ("memory","growth","career","capability"): return build_response(False, error={"code":"INVALID_TYPE","message":"invalid handoff_type"})
    ok, data, _ = _run_memory_cmd([str(script_path), "handoff-create", "--packet-id", src_id, "--handoff-type", htype])
    if not ok: return build_response(False, error={"code":"SCRIPT_ERROR","message":data.get("error","unknown")})
    msg = "Memory handoff creates candidate only — NOT written to memory store." if htype=="memory" else ""
    return build_response(True, data={"handoff_type": htype, "status": data.get("status","created"), "note": msg})

def handle_research_archive_post(body, script_path):
    ttype = (body.get("target_type") or "").strip()
    tid = (body.get("target_id") or "").strip()
    if not ttype or not tid: return build_response(False, error={"code":"MISSING_ARGS","message":"target_type and target_id required"})
    if ttype not in ("source","packet","cognition_card","handoff"): return build_response(False, error={"code":"INVALID_TYPE","message":"invalid target_type"})
    if ttype == "cognition_card":
        ok, data, _ = _run_memory_cmd([str(COGNITION_CARD_SCRIPT), "archive", "--card-id", tid])
    else:
        ok, data, _ = _run_memory_cmd([str(script_path), "source-archive", "--source-id", tid])
    return build_response(True, data={"target_id": tid, "target_type": ttype, "status": "archived" if ok else "error"})


# --- Growth API handlers ---

def _redact_growth_value(value):
    if isinstance(value, str):
        is_redacted, redacted = _redact(value)
        return redacted if is_redacted else value
    if isinstance(value, list):
        return [_redact_growth_value(v) for v in value]
    if isinstance(value, dict):
        return _redact_growth_record(value)
    return value


def _redact_growth_record(record):
    redacted = {}
    touched = False
    for key, value in (record or {}).items():
        safe_value = _redact_growth_value(value)
        if safe_value == "[REDACTED]":
            touched = True
        redacted[key] = safe_value
    if touched:
        redacted["redacted"] = True
    return redacted


def _growth_get(path, key, limit):
    results, skipped = read_jsonl(path, limit)
    safe = [_redact_growth_record(r) for r in results]
    return build_response(True, data={key: safe[-limit:]}, meta_extra={
        "total": len(safe),
        "skipped": skipped,
        "limit": limit,
        "source": _safe_source(path, "none") if path.exists() else "none",
    })


def handle_growth_candidates_get(path, limit):
    return _growth_get(path, "candidates", limit)


def handle_growth_goals_get(path, limit):
    return _growth_get(path, "goals", limit)


def handle_growth_capacity_get(path, limit):
    return _growth_get(path, "capacity", limit)


def handle_growth_weekly_get(path, limit):
    return _growth_get(path, "weekly_plans", limit)


def handle_growth_tasks_get(path, limit):
    return _growth_get(path, "daily_tasks", limit)


def handle_growth_reviews_get(path, limit):
    return _growth_get(path, "reviews", limit)


def handle_growth_adjustments_get(path, limit):
    return _growth_get(path, "adjustments", limit)


def handle_growth_handoffs_get(path, limit):
    return _growth_get(path, "handoffs", limit)


def _run_growth_cmd(cmd_args, timeout=30):
    return _run_memory_cmd(cmd_args, timeout=timeout)


def _script_error(data, code="SCRIPT_ERROR"):
    msg = data.get("error") or data.get("reason") or "growth script failed"
    return build_response(False, error={"code": code, "message": str(msg)})


def _csv(value):
    if isinstance(value, list):
        return ",".join(str(v).strip() for v in value if str(v).strip())
    return str(value or "")


def _status_for(resp):
    if resp.get("ok"):
        return 200
    code = (resp.get("error") or {}).get("code")
    return 404 if code in {"CANDIDATE_NOT_FOUND", "GOAL_NOT_FOUND", "TASK_NOT_FOUND", "NOT_FOUND"} else 400


def handle_growth_candidates_post(body, script_path, candidates_path=GROWTH_CANDIDATES_PATH, audit_path=GROWTH_AUDIT_PATH):
    title = (body.get("title") or "").strip()
    reason = (body.get("reason") or "").strip()
    if not title:
        return build_response(False, error={"code": "EMPTY_TITLE", "message": "title must not be empty"})
    if len(title) > MAX_GROWTH_CONTENT or len(reason) > MAX_GROWTH_CONTENT:
        return build_response(False, error={"code": "CONTENT_TOO_LONG", "message": f"growth content must be <= {MAX_GROWTH_CONTENT} chars"})
    if _redact(title)[0] or _redact(reason)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})

    ok, data, ec = _run_growth_cmd([
        str(script_path), "candidate-create",
        "--source-type", body.get("source_type", "manual"),
        "--title", title,
        "--goal-area", body.get("goal_area", "other"),
        "--reason", reason,
        "--confidence", str(body.get("confidence", 0.5)),
        "--priority", body.get("priority", "P2"),
        "--candidates-log", str(candidates_path),
        "--audit-log", str(audit_path),
    ])
    if not ok or ec != 0 or data.get("status") == "rejected":
        code = "SECRET_DETECTED" if data.get("reason") == "secret" else "SCRIPT_ERROR"
        return _script_error(data, code)
    return build_response(True, data={"candidate_id": data.get("candidate", {}).get("candidate_id"), "status": data.get("status")})


def handle_growth_candidate_accept_post(body, script_path, candidates_path=GROWTH_CANDIDATES_PATH, audit_path=GROWTH_AUDIT_PATH):
    cid = (body.get("candidate_id") or "").strip()
    if not cid:
        return build_response(False, error={"code": "MISSING_ID", "message": "candidate_id required"})
    ok, data, ec = _run_growth_cmd([str(script_path), "candidate-accept", "--candidate-id", cid, "--candidates-log", str(candidates_path), "--audit-log", str(audit_path)])
    if not ok or ec != 0:
        return _script_error(data, "CANDIDATE_NOT_FOUND" if data.get("error") == "not found" else "SCRIPT_ERROR")
    return build_response(True, data={"candidate_id": cid, "status": data.get("status", "accepted")})


def handle_growth_candidate_reject_post(body, script_path, candidates_path=GROWTH_CANDIDATES_PATH, audit_path=GROWTH_AUDIT_PATH):
    cid = (body.get("candidate_id") or "").strip()
    if not cid:
        return build_response(False, error={"code": "MISSING_ID", "message": "candidate_id required"})
    ok, data, ec = _run_growth_cmd([str(script_path), "candidate-reject", "--candidate-id", cid, "--reason", body.get("reason", "rejected"), "--candidates-log", str(candidates_path), "--audit-log", str(audit_path)])
    if not ok or ec != 0:
        return _script_error(data, "CANDIDATE_NOT_FOUND" if data.get("error") == "not found" else "SCRIPT_ERROR")
    return build_response(True, data={"candidate_id": cid, "status": data.get("status", "rejected")})


def handle_growth_goals_post(body, script_path, candidates_path=GROWTH_CANDIDATES_PATH, goals_path=GROWTH_GOALS_PATH, audit_path=GROWTH_AUDIT_PATH):
    cid = (body.get("candidate_id") or "").strip()
    success = (body.get("success_criteria") or "").strip()
    if not cid:
        return build_response(False, error={"code": "MISSING_ID", "message": "candidate_id required"})
    if not success:
        return build_response(False, error={"code": "MISSING_SUCCESS", "message": "success_criteria required"})
    if _redact(success)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    ok, data, ec = _run_growth_cmd([
        str(script_path), "goal-create",
        "--candidate-id", cid,
        "--success-criteria", success,
        "--minimum-result", body.get("minimum_result", body.get("minimum_viable_result", "")),
        "--priority", body.get("priority", "P2"),
        "--candidates-log", str(candidates_path),
        "--goals-log", str(goals_path),
        "--audit-log", str(audit_path),
    ])
    if not ok or ec != 0:
        err = data.get("error")
        if err == "candidate not found":
            return _script_error(data, "CANDIDATE_NOT_FOUND")
        if err == "candidate not accepted":
            return _script_error(data, "NOT_ACCEPTED")
        return _script_error(data)
    return build_response(True, data={"goal_id": data.get("goal", {}).get("goal_id"), "status": data.get("status")})


def handle_growth_capacity_post(body, script_path, capacity_path=GROWTH_CAPACITY_PATH, audit_path=GROWTH_AUDIT_PATH):
    try:
        hours = float(body.get("available_hours", 8))
    except (TypeError, ValueError):
        return build_response(False, error={"code": "INVALID_HOURS", "message": "available_hours must be numeric"})
    ok, data, ec = _run_growth_cmd([
        str(script_path), "capacity-create",
        "--period-type", body.get("period_type", "weekly"),
        "--available-hours", str(hours),
        "--focus-slots", str(body.get("focus_slots", 2)),
        "--energy-level", body.get("energy_level", "medium"),
        "--active-goal-ids", _csv(body.get("active_goal_ids", "")),
        "--capacity-log", str(capacity_path),
        "--audit-log", str(audit_path),
    ])
    if not ok or ec != 0:
        return _script_error(data)
    return build_response(True, data={"budget_id": data.get("budget", {}).get("budget_id"), "overload_warning": data.get("overload_warning"), "status": data.get("status")})


def handle_growth_weekly_post(body, script_path, weekly_path=GROWTH_WEEKLY_PATH, audit_path=GROWTH_AUDIT_PATH):
    week_start = (body.get("week_start") or "").strip()
    if not week_start:
        return build_response(False, error={"code": "MISSING_WEEK_START", "message": "week_start required"})
    ok, data, ec = _run_growth_cmd([
        str(script_path), "weekly-create",
        "--week-start", week_start,
        "--goal-ids", _csv(body.get("goal_ids", "")),
        "--focus-theme", body.get("focus_theme", ""),
        "--weekly-log", str(weekly_path),
        "--audit-log", str(audit_path),
    ])
    if not ok or ec != 0:
        return _script_error(data)
    return build_response(True, data={"weekly_plan_id": data.get("weekly_plan", {}).get("weekly_plan_id"), "status": data.get("status")})


def handle_growth_tasks_post(body, script_path, tasks_path=GROWTH_TASKS_PATH, audit_path=GROWTH_AUDIT_PATH):
    title = (body.get("title") or "").strip()
    goal_id = (body.get("goal_id") or "").strip()
    date = (body.get("date") or "").strip()
    if not title:
        return build_response(False, error={"code": "EMPTY_TITLE", "message": "title must not be empty"})
    if not goal_id or not date:
        return build_response(False, error={"code": "MISSING_ARGS", "message": "date and goal_id required"})
    if len(title) > MAX_GROWTH_CONTENT:
        return build_response(False, error={"code": "CONTENT_TOO_LONG", "message": f"title must be <= {MAX_GROWTH_CONTENT} chars"})
    if _redact(title)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    ok, data, ec = _run_growth_cmd([
        str(script_path), "task-create",
        "--date", date,
        "--goal-id", goal_id,
        "--title", title,
        "--task-type", body.get("task_type", "study"),
        "--estimated-minutes", str(body.get("estimated_minutes", 30)),
        "--tasks-log", str(tasks_path),
        "--audit-log", str(audit_path),
    ])
    if not ok or ec != 0:
        return _script_error(data)
    return build_response(True, data={"task_id": data.get("task", {}).get("task_id"), "status": data.get("status")})


def handle_growth_task_status_post(body, script_path, tasks_path=GROWTH_TASKS_PATH, audit_path=GROWTH_AUDIT_PATH):
    tid = (body.get("task_id") or "").strip()
    status = (body.get("status") or "").strip()
    if not tid or not status:
        return build_response(False, error={"code": "MISSING_ARGS", "message": "task_id and status required"})
    ok, data, ec = _run_growth_cmd([str(script_path), "task-status", "--task-id", tid, "--status", status, "--tasks-log", str(tasks_path), "--audit-log", str(audit_path)])
    if not ok or ec != 0:
        return _script_error(data, "TASK_NOT_FOUND" if data.get("error") == "not found" else "SCRIPT_ERROR")
    return build_response(True, data={"task_id": tid, "status": data.get("new_status", status)})


def handle_growth_reviews_post(body, script_path, reviews_path=GROWTH_REVIEWS_PATH, audit_path=GROWTH_AUDIT_PATH):
    gid = (body.get("goal_id") or "").strip()
    if not gid:
        return build_response(False, error={"code": "MISSING_ID", "message": "goal_id required"})
    ok, data, ec = _run_growth_cmd([
        str(script_path), "review-create",
        "--goal-id", gid,
        "--period-type", body.get("period_type", "weekly"),
        "--self-rating", str(body.get("self_rating", 3)),
        "--blockers", body.get("blockers", ""),
        "--lessons", body.get("lessons", body.get("lessons_learned", "")),
        "--evidence", body.get("evidence", body.get("evidence_summary", "")),
        "--adjustment-needed", str(int(bool(body.get("adjustment_needed", False)))),
        "--reviews-log", str(reviews_path),
        "--audit-log", str(audit_path),
    ])
    if not ok or ec != 0:
        return _script_error(data)
    return build_response(True, data={"review_id": data.get("review", {}).get("review_id"), "repeated_blocker": data.get("repeated_blocker"), "status": data.get("status")})


def handle_growth_adjustments_post(body, script_path, adjustments_path=GROWTH_ADJUSTMENTS_PATH, audit_path=GROWTH_AUDIT_PATH):
    gid = (body.get("goal_id") or "").strip()
    proposal_type = (body.get("proposal_type") or "").strip()
    if not gid or not proposal_type:
        return build_response(False, error={"code": "MISSING_ARGS", "message": "goal_id and proposal_type required"})
    reason = (body.get("reason") or "").strip()
    if len(reason) > MAX_GROWTH_CONTENT:
        return build_response(False, error={"code": "CONTENT_TOO_LONG", "message": f"reason must be <= {MAX_GROWTH_CONTENT} chars"})
    if _redact(reason)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    ok, data, ec = _run_growth_cmd([
        str(script_path), "adjustment-create",
        "--goal-id", gid,
        "--proposal-type", proposal_type,
        "--reason", reason,
        "--proposed-change", body.get("proposed_change", ""),
        "--impact", body.get("impact", "medium"),
        "--adjustments-log", str(adjustments_path),
        "--audit-log", str(audit_path),
    ])
    if not ok or ec != 0:
        return _script_error(data)
    adj = data.get("adjustment", {})
    return build_response(True, data={"proposal_id": adj.get("proposal_id"), "approval_required": adj.get("approval_required"), "risk_level": adj.get("risk_level"), "status": data.get("status")})


def handle_growth_handoffs_post(body, script_path, audit_path=GROWTH_AUDIT_PATH):
    gid = (body.get("goal_id") or "").strip()
    if not gid:
        return build_response(False, error={"code": "MISSING_ID", "message": "goal_id required"})
    notes = (body.get("notes") or "").strip()
    if _redact(notes)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    ok, data, ec = _run_growth_cmd([str(script_path), "memory-handoff", "--goal-id", gid, "--notes", notes, "--audit-log", str(audit_path)])
    if not ok or ec != 0:
        return _script_error(data)
    return build_response(True, data={"goal_id": gid, "status": data.get("status"), "delegated_to": data.get("delegated_to"), "note": "candidate only; not written to memory store"})


def handle_growth_archive_post(body, script_path, goals_path=GROWTH_GOALS_PATH, audit_path=GROWTH_AUDIT_PATH):
    gid = (body.get("goal_id") or "").strip()
    if not gid:
        return build_response(False, error={"code": "MISSING_ID", "message": "goal_id required"})
    ok, data, ec = _run_growth_cmd([str(script_path), "goal-archive", "--goal-id", gid, "--goals-log", str(goals_path), "--audit-log", str(audit_path)])
    if not ok or ec != 0:
        return _script_error(data, "GOAL_NOT_FOUND" if data.get("error") == "not found" else "SCRIPT_ERROR")
    return build_response(True, data={"goal_id": gid, "status": data.get("status", "archived")})


# --- Career API handlers ---

def _career_get(path, key, limit):
    results, skipped = read_jsonl(path, limit)
    safe = [_redact_growth_record(r) for r in results]
    return build_response(True, data={key: safe[-limit:]}, meta_extra={
        "total": len(safe),
        "skipped": skipped,
        "limit": limit,
        "source": _safe_source(path, "none") if path.exists() else "none",
    })


def handle_career_assets_get(path, limit):
    return _career_get(path, "assets", limit)


def handle_career_claims_get(path, limit):
    return _career_get(path, "claims", limit)


def handle_career_jds_get(path, limit):
    return _career_get(path, "jds", limit)


def handle_career_evaluations_get(path, limit):
    return _career_get(path, "evaluations", limit)


def handle_career_applications_get(path, limit):
    return _career_get(path, "applications", limit)


def handle_career_handoffs_get(path, limit):
    return _career_get(path, "handoffs", limit)


def _career_paths(assets_path, claims_path, jds_path, evaluations_path, applications_path, handoffs_path, audit_path):
    return [
        "--assets-log", str(assets_path),
        "--claims-log", str(claims_path),
        "--jds-log", str(jds_path),
        "--evaluations-log", str(evaluations_path),
        "--applications-log", str(applications_path),
        "--handoffs-log", str(handoffs_path),
        "--audit-log", str(audit_path),
    ]


def handle_career_assets_post(body, script_path, assets_path=CAREER_ASSETS_PATH, claims_path=CAREER_CLAIMS_PATH,
                              jds_path=CAREER_JDS_PATH, evaluations_path=CAREER_EVALUATIONS_PATH,
                              applications_path=CAREER_APPLICATIONS_PATH, handoffs_path=CAREER_HANDOFFS_PATH,
                              audit_path=CAREER_AUDIT_PATH):
    title = (body.get("title") or "").strip()
    summary = (body.get("summary") or "").strip()
    if not title:
        return build_response(False, error={"code": "EMPTY_TITLE", "message": "title required"})
    if _redact(title)[0] or _redact(summary)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    args = [str(script_path), "asset-create", "--asset-type", body.get("asset_type", "project"),
            "--title", title, "--summary", summary, "--evidence-refs", _csv(body.get("evidence_refs", "")),
            "--source-refs", _csv(body.get("source_refs", ""))]
    args.extend(_career_paths(assets_path, claims_path, jds_path, evaluations_path, applications_path, handoffs_path, audit_path))
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return _script_error(data)
    return build_response(True, data={"asset_id": data.get("asset", {}).get("asset_id"), "status": data.get("asset", {}).get("status")})


def handle_career_claims_post(body, script_path, assets_path=CAREER_ASSETS_PATH, claims_path=CAREER_CLAIMS_PATH,
                              jds_path=CAREER_JDS_PATH, evaluations_path=CAREER_EVALUATIONS_PATH,
                              applications_path=CAREER_APPLICATIONS_PATH, handoffs_path=CAREER_HANDOFFS_PATH,
                              audit_path=CAREER_AUDIT_PATH):
    claim_text = (body.get("claim_text") or "").strip()
    if not claim_text:
        return build_response(False, error={"code": "EMPTY_CLAIM", "message": "claim_text required"})
    if _redact(claim_text)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    args = [str(script_path), "claim-create", "--claim-text", claim_text,
            "--evidence-refs", _csv(body.get("evidence_refs", "")), "--asset-refs", _csv(body.get("asset_refs", ""))]
    args.extend(_career_paths(assets_path, claims_path, jds_path, evaluations_path, applications_path, handoffs_path, audit_path))
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return _script_error(data)
    return build_response(True, data={"claim_id": data.get("claim", {}).get("claim_id"), "status": data.get("claim", {}).get("status")})


def handle_career_jds_post(body, script_path, assets_path=CAREER_ASSETS_PATH, claims_path=CAREER_CLAIMS_PATH,
                           jds_path=CAREER_JDS_PATH, evaluations_path=CAREER_EVALUATIONS_PATH,
                           applications_path=CAREER_APPLICATIONS_PATH, handoffs_path=CAREER_HANDOFFS_PATH,
                           audit_path=CAREER_AUDIT_PATH):
    title = (body.get("title") or "").strip()
    if not title:
        return build_response(False, error={"code": "EMPTY_TITLE", "message": "title required"})
    if _redact(title)[0] or _redact(body.get("description_summary", ""))[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    args = [str(script_path), "jd-create", "--title", title,
            "--company", body.get("company", ""), "--description-summary", body.get("description_summary", ""),
            "--requirements", _csv(body.get("requirements", ""))]
    args.extend(_career_paths(assets_path, claims_path, jds_path, evaluations_path, applications_path, handoffs_path, audit_path))
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return _script_error(data)
    return build_response(True, data={"jd_id": data.get("jd", {}).get("jd_id"), "status": data.get("jd", {}).get("status")})


def handle_career_evaluations_post(body, script_path, assets_path=CAREER_ASSETS_PATH, claims_path=CAREER_CLAIMS_PATH,
                                   jds_path=CAREER_JDS_PATH, evaluations_path=CAREER_EVALUATIONS_PATH,
                                   applications_path=CAREER_APPLICATIONS_PATH, handoffs_path=CAREER_HANDOFFS_PATH,
                                   audit_path=CAREER_AUDIT_PATH):
    jd_id = (body.get("jd_id") or "").strip()
    if not jd_id:
        return build_response(False, error={"code": "MISSING_ID", "message": "jd_id required"})
    args = [str(script_path), "jd-evaluate", "--jd-id", jd_id]
    args.extend(_career_paths(assets_path, claims_path, jds_path, evaluations_path, applications_path, handoffs_path, audit_path))
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return _script_error(data, "JD_NOT_FOUND" if data.get("status") == "not_found" else "SCRIPT_ERROR")
    ev = data.get("evaluation", {})
    return build_response(True, data={"evaluation_id": ev.get("evaluation_id"), "score": ev.get("score"), "status": ev.get("status")})


def handle_career_applications_post(body, script_path, assets_path=CAREER_ASSETS_PATH, claims_path=CAREER_CLAIMS_PATH,
                                    jds_path=CAREER_JDS_PATH, evaluations_path=CAREER_EVALUATIONS_PATH,
                                    applications_path=CAREER_APPLICATIONS_PATH, handoffs_path=CAREER_HANDOFFS_PATH,
                                    audit_path=CAREER_AUDIT_PATH):
    jd_id = (body.get("jd_id") or "").strip()
    notes = (body.get("notes") or "").strip()
    if not jd_id:
        return build_response(False, error={"code": "MISSING_ID", "message": "jd_id required"})
    if _redact(notes)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    args = [str(script_path), "application-create", "--jd-id", jd_id,
            "--asset-refs", _csv(body.get("asset_refs", "")), "--claim-refs", _csv(body.get("claim_refs", "")),
            "--notes", notes]
    args.extend(_career_paths(assets_path, claims_path, jds_path, evaluations_path, applications_path, handoffs_path, audit_path))
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return _script_error(data, "JD_NOT_FOUND" if data.get("status") == "not_found" else "SCRIPT_ERROR")
    app = data.get("application", {})
    return build_response(True, data={"application_id": app.get("application_id"), "status": app.get("status"), "auto_submit": app.get("auto_submit")})


def handle_career_handoffs_post(body, script_path, assets_path=CAREER_ASSETS_PATH, claims_path=CAREER_CLAIMS_PATH,
                                jds_path=CAREER_JDS_PATH, evaluations_path=CAREER_EVALUATIONS_PATH,
                                applications_path=CAREER_APPLICATIONS_PATH, handoffs_path=CAREER_HANDOFFS_PATH,
                                audit_path=CAREER_AUDIT_PATH):
    source_id = (body.get("source_id") or "").strip()
    summary = (body.get("summary") or "").strip()
    if not source_id:
        return build_response(False, error={"code": "MISSING_ID", "message": "source_id required"})
    if _redact(summary)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    args = [str(script_path), "handoff-create", "--source-type", body.get("source_type", "manual"),
            "--source-id", source_id, "--summary", summary]
    args.extend(_career_paths(assets_path, claims_path, jds_path, evaluations_path, applications_path, handoffs_path, audit_path))
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return _script_error(data)
    return build_response(True, data={"handoff_id": data.get("handoff", {}).get("handoff_id"), "status": data.get("status")})


# --- Readiness Center API handlers (Tasks 16-20) ---

def _readiness_get(path, key, limit):
    results, skipped = read_jsonl(path, limit)
    safe = [_redact_growth_record(r) for r in results]
    return build_response(True, data={key: safe[-limit:]}, meta_extra={
        "total": len(safe),
        "skipped": skipped,
        "limit": limit,
        "source": _safe_source(path, "none") if path.exists() else "none",
    })


def _readiness_paths(workflows_path, runs_path, skills_path, skill_reviews_path, nodes_path,
                     edges_path, boundaries_path, state_path, routes_path, costs_path,
                     mcp_profiles_path, tool_policies_path, audit_path):
    return [
        "--workflows-log", str(workflows_path),
        "--runs-log", str(runs_path),
        "--skills-log", str(skills_path),
        "--skill-reviews-log", str(skill_reviews_path),
        "--nodes-log", str(nodes_path),
        "--edges-log", str(edges_path),
        "--boundaries-log", str(boundaries_path),
        "--state-log", str(state_path),
        "--model-routes-log", str(routes_path),
        "--cost-events-log", str(costs_path),
        "--mcp-profiles-log", str(mcp_profiles_path),
        "--tool-policies-log", str(tool_policies_path),
        "--audit-log", str(audit_path),
    ]


def _readiness_call(script_path, command, cmd_args, paths):
    args = [str(script_path), command] + cmd_args + _readiness_paths(*paths)
    ok, data, ec = _run_memory_cmd(args)
    if not ok or ec != 0:
        return False, data
    return True, data


def _readiness_default_paths(workflows_path=AUTOMATION_WORKFLOWS_PATH, runs_path=AUTOMATION_RUNS_PATH,
                             skills_path=SKILL_CANDIDATES_PATH, skill_reviews_path=SKILL_REVIEWS_PATH,
                             nodes_path=KNOWLEDGE_NODES_PATH, edges_path=KNOWLEDGE_EDGES_PATH,
                             boundaries_path=KNOWLEDGE_BOUNDARIES_PATH, state_path=KNOWLEDGE_STATE_PATH,
                             routes_path=MODEL_ROUTES_PATH, costs_path=COST_EVENTS_PATH,
                             mcp_profiles_path=MCP_PROFILES_PATH, tool_policies_path=TOOL_POLICIES_PATH,
                             audit_path=READINESS_AUDIT_PATH):
    return (workflows_path, runs_path, skills_path, skill_reviews_path, nodes_path, edges_path,
            boundaries_path, state_path, routes_path, costs_path, mcp_profiles_path,
            tool_policies_path, audit_path)


def handle_automation_workflows_get(path, limit):
    return _readiness_get(path, "workflows", limit)


def handle_automation_runs_get(path, limit):
    return _readiness_get(path, "runs", limit)


def handle_skill_candidates_get(path, limit):
    return _readiness_get(path, "skills", limit)


def handle_skill_reviews_get(path, limit):
    return _readiness_get(path, "skill_reviews", limit)


def handle_knowledge_nodes_get(path, limit):
    return _readiness_get(path, "nodes", limit)


def handle_knowledge_edges_get(path, limit):
    return _readiness_get(path, "edges", limit)


def handle_knowledge_boundaries_get(path, limit):
    return _readiness_get(path, "boundaries", limit)


def handle_knowledge_state_get(path, limit):
    return _readiness_get(path, "knowledge_state", limit)


def handle_model_routes_get(path, limit):
    return _readiness_get(path, "model_routes", limit)


def handle_cost_events_get(path, limit):
    return _readiness_get(path, "cost_events", limit)


def handle_mcp_profiles_get(path, limit):
    return _readiness_get(path, "mcp_profiles", limit)


def handle_tool_policies_get(path, limit):
    return _readiness_get(path, "tool_policies", limit)


def handle_automation_workflows_post(body, script_path, paths=None):
    name = (body.get("name") or "").strip()
    if not name:
        return build_response(False, error={"code": "EMPTY_NAME", "message": "name required"})
    if _redact(name)[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    ok, data = _readiness_call(script_path, "workflow-create", [
        "--name", name,
        "--trigger-type", body.get("trigger_type", "manual"),
        "--action-refs", _csv(body.get("action_refs", "")),
        "--risk-level", body.get("risk_level", "R2"),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data)
    wf = data.get("workflow", {})
    return build_response(True, data={"workflow_id": wf.get("workflow_id"), "enabled": wf.get("enabled"), "approval_required": wf.get("approval_required")})


def handle_automation_runs_post(body, script_path, paths=None):
    workflow_id = (body.get("workflow_id") or "").strip()
    if not workflow_id:
        return build_response(False, error={"code": "MISSING_ID", "message": "workflow_id required"})
    ok, data = _readiness_call(script_path, "workflow-trigger", [
        "--workflow-id", workflow_id,
        "--triggered-by", body.get("triggered_by", "user"),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data, "WORKFLOW_NOT_FOUND" if data.get("status") == "not_found" else "SCRIPT_ERROR")
    run = data.get("run", {})
    return build_response(True, data={"workflow_run_id": run.get("workflow_run_id"), "status": run.get("status"), "output_refs": run.get("output_refs", [])})


def handle_skill_candidates_post(body, script_path, paths=None):
    name = (body.get("name") or "").strip()
    if not name:
        return build_response(False, error={"code": "EMPTY_NAME", "message": "name required"})
    if _redact(name)[0] or _redact(body.get("description", ""))[0]:
        return build_response(False, error={"code": "SECRET_DETECTED", "message": "secret-like content rejected"})
    ok, data = _readiness_call(script_path, "skill-candidate", [
        "--name", name,
        "--description", body.get("description", ""),
        "--risk-level", body.get("risk_level", "R2"),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data)
    skill = data.get("skill", {})
    return build_response(True, data={"skill_id": skill.get("skill_id"), "enabled": skill.get("enabled"), "sandbox_status": skill.get("sandbox_status")})


def handle_skill_reviews_post(body, script_path, paths=None):
    skill_id = (body.get("skill_id") or "").strip()
    if not skill_id:
        return build_response(False, error={"code": "MISSING_ID", "message": "skill_id required"})
    ok, data = _readiness_call(script_path, "skill-review", [
        "--skill-id", skill_id,
        "--result", body.get("result", "passed"),
        "--notes", body.get("notes", ""),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data, "SKILL_NOT_FOUND" if data.get("status") == "not_found" else "SCRIPT_ERROR")
    review = data.get("review", {})
    return build_response(True, data={"skill_review_id": review.get("skill_review_id"), "enabled_after_review": review.get("enabled_after_review")})


def handle_knowledge_nodes_post(body, script_path, paths=None):
    label = (body.get("label") or "").strip()
    if not label:
        return build_response(False, error={"code": "EMPTY_LABEL", "message": "label required"})
    ok, data = _readiness_call(script_path, "kg-node", [
        "--label", label,
        "--node-type", body.get("node_type", "concept"),
        "--summary", body.get("summary", ""),
        "--source-refs", _csv(body.get("source_refs", "")),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data)
    node = data.get("node", {})
    return build_response(True, data={"node_id": node.get("node_id"), "status": node.get("status")})


def handle_knowledge_edges_post(body, script_path, paths=None):
    from_ref = (body.get("from_node_ref") or "").strip()
    to_ref = (body.get("to_node_ref") or "").strip()
    if not from_ref or not to_ref:
        return build_response(False, error={"code": "MISSING_ID", "message": "from_node_ref and to_node_ref required"})
    ok, data = _readiness_call(script_path, "kg-edge", [
        "--from-node-ref", from_ref,
        "--to-node-ref", to_ref,
        "--relation", body.get("relation", "relates_to"),
        "--source-refs", _csv(body.get("source_refs", "")),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data, "NODE_NOT_FOUND" if data.get("status") == "not_found" else "SCRIPT_ERROR")
    edge = data.get("edge", {})
    return build_response(True, data={"edge_id": edge.get("edge_id"), "status": edge.get("status")})


def handle_knowledge_boundaries_post(body, script_path, paths=None):
    summary = (body.get("summary") or "").strip()
    if not summary:
        return build_response(False, error={"code": "EMPTY_SUMMARY", "message": "summary required"})
    ok, data = _readiness_call(script_path, "boundary-create", [
        "--summary", summary,
        "--boundary-type", body.get("boundary_type", "open_question"),
        "--source-refs", _csv(body.get("source_refs", "")),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data)
    boundary = data.get("boundary", {})
    return build_response(True, data={"boundary_id": boundary.get("boundary_id"), "status": boundary.get("status")})


def handle_knowledge_state_post(body, script_path, paths=None):
    ok, data = _readiness_call(script_path, "kg-state", [], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data)
    state = data.get("knowledge_state", {})
    return build_response(True, data={"knowledge_state_id": state.get("knowledge_state_id"), "rag_enabled": state.get("rag_enabled"), "node_count": state.get("node_count")})


def handle_model_routes_post(body, script_path, paths=None):
    task_type = (body.get("task_type") or "").strip()
    if not task_type:
        return build_response(False, error={"code": "EMPTY_TASK_TYPE", "message": "task_type required"})
    ok, data = _readiness_call(script_path, "model-route", [
        "--task-type", task_type,
        "--default-model", body.get("default_model", "local/manual"),
        "--budget-class", body.get("budget_class", "medium"),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data)
    route = data.get("route", {})
    return build_response(True, data={"router_id": route.get("router_id"), "litellm_enabled": route.get("litellm_enabled")})


def handle_cost_events_post(body, script_path, paths=None):
    task_ref = (body.get("task_ref") or "").strip()
    if not task_ref:
        return build_response(False, error={"code": "MISSING_ID", "message": "task_ref required"})
    ok, data = _readiness_call(script_path, "cost-event", [
        "--task-ref", task_ref,
        "--model", body.get("model", "local/manual"),
        "--estimated-cost-usd", str(body.get("estimated_cost_usd", 0)),
        "--budget-class", body.get("budget_class", "low"),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data)
    event = data.get("cost_event", {})
    return build_response(True, data={"cost_event_id": event.get("cost_event_id"), "estimated_cost_usd": event.get("estimated_cost_usd")})


def handle_mcp_profiles_post(body, script_path, paths=None):
    name = (body.get("name") or "").strip()
    if not name:
        return build_response(False, error={"code": "EMPTY_NAME", "message": "name required"})
    ok, data = _readiness_call(script_path, "mcp-profile", [
        "--name", name,
        "--trust-level", body.get("trust_level", "unverified"),
        "--allowed-tools", _csv(body.get("allowed_tools", "")),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data)
    profile = data.get("profile", {})
    return build_response(True, data={"mcp_profile_id": profile.get("mcp_profile_id"), "enabled": profile.get("enabled"), "write_actions_allowed": profile.get("write_actions_allowed")})


def handle_tool_policies_post(body, script_path, paths=None):
    tool_ref = (body.get("tool_ref") or "").strip()
    if not tool_ref:
        return build_response(False, error={"code": "MISSING_ID", "message": "tool_ref required"})
    ok, data = _readiness_call(script_path, "tool-policy", [
        "--tool-ref", tool_ref,
        "--trust-level", body.get("trust_level", "local_sandbox_tool"),
    ], paths or _readiness_default_paths())
    if not ok:
        return _script_error(data)
    policy = data.get("policy", {})
    return build_response(True, data={"tool_trust_policy_id": policy.get("tool_trust_policy_id"), "write_allowed": policy.get("write_allowed"), "approval_required": policy.get("approval_required")})


class OnePalHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OnePal API."""

    # Paths overrideable for testing
    health_path = HEALTH_PATH
    tasks_path = TASKS_PATH
    trees_path = TREES_PATH
    task_runs_path = TASK_RUNS_PATH
    mas_trace_path = MAS_TRACE_PATH
    gateway_path = COMMAND_GATEWAY
    memory_candidate_script = MEMORY_CANDIDATE_SCRIPT
    memory_store_script = MEMORY_STORE_SCRIPT
    memory_governance_script = MEMORY_GOVERNANCE_SCRIPT
    memory_candidates_path = MEMORY_CANDIDATES_PATH
    memory_proposals_path = MEMORY_PROPOSALS_PATH
    memory_store_path = MEMORY_STORE_PATH
    memory_reviews_path = MEMORY_REVIEWS_PATH
    memory_conflicts_path = MEMORY_CONFLICTS_PATH
    memory_changes_path = MEMORY_CHANGES_PATH
    memory_snapshots_path = MEMORY_SNAPSHOTS_PATH
    memory_snapshot_dir = MEMORY_SNAPSHOT_DIR
    memory_audit_path = PROJECT_ROOT / "logs" / "memory_audit.jsonl"
    research_sources_path = RESEARCH_SOURCES_PATH
    research_packets_path = RESEARCH_PACKETS_PATH
    research_evidence_path = RESEARCH_EVIDENCE_PATH
    research_cards_path = RESEARCH_CARDS_PATH
    research_packet_script = RESEARCH_PACKET_SCRIPT
    cognition_card_script = COGNITION_CARD_SCRIPT
    growth_goal_script = GROWTH_GOAL_SCRIPT
    growth_plan_script = GROWTH_PLAN_SCRIPT
    growth_review_script = GROWTH_REVIEW_SCRIPT
    growth_candidates_path = GROWTH_CANDIDATES_PATH
    growth_goals_path = GROWTH_GOALS_PATH
    growth_capacity_path = GROWTH_CAPACITY_PATH
    growth_weekly_path = GROWTH_WEEKLY_PATH
    growth_tasks_path = GROWTH_TASKS_PATH
    growth_reviews_path = GROWTH_REVIEWS_PATH
    growth_adjustments_path = GROWTH_ADJUSTMENTS_PATH
    growth_handoffs_path = GROWTH_HANDOFFS_PATH
    growth_audit_path = GROWTH_AUDIT_PATH
    career_center_script = CAREER_CENTER_SCRIPT
    career_assets_path = CAREER_ASSETS_PATH
    career_claims_path = CAREER_CLAIMS_PATH
    career_jds_path = CAREER_JDS_PATH
    career_evaluations_path = CAREER_EVALUATIONS_PATH
    career_applications_path = CAREER_APPLICATIONS_PATH
    career_handoffs_path = CAREER_HANDOFFS_PATH
    career_audit_path = CAREER_AUDIT_PATH
    readiness_center_script = READINESS_CENTER_SCRIPT
    automation_workflows_path = AUTOMATION_WORKFLOWS_PATH
    automation_runs_path = AUTOMATION_RUNS_PATH
    skill_candidates_path = SKILL_CANDIDATES_PATH
    skill_reviews_path = SKILL_REVIEWS_PATH
    knowledge_nodes_path = KNOWLEDGE_NODES_PATH
    knowledge_edges_path = KNOWLEDGE_EDGES_PATH
    knowledge_boundaries_path = KNOWLEDGE_BOUNDARIES_PATH
    knowledge_state_path = KNOWLEDGE_STATE_PATH
    model_routes_path = MODEL_ROUTES_PATH
    cost_events_path = COST_EVENTS_PATH
    mcp_profiles_path = MCP_PROFILES_PATH
    tool_policies_path = TOOL_POLICIES_PATH
    readiness_audit_path = READINESS_AUDIT_PATH

    def _send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_query_limit(self):
        """Extract ?limit=N from query string."""
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        try:
            limit = int(qs.get("limit", [20])[0])
            limit = min(max(limit, 1), MAX_LIMIT)
        except (ValueError, TypeError):
            limit = 20
        return limit, parsed.path

    def do_GET(self):
        path = urlparse(self.path).path
        limit, _ = self._parse_query_limit()

        try:
            if path == "/health":
                resp = handle_health(self.health_path)
                self._send_json(200, resp)

            elif path == "/tasks":
                resp = handle_tasks(self.tasks_path, limit)
                self._send_json(200, resp)

            elif path == "/task-trees":
                resp = handle_task_trees(self.trees_path, limit)
                self._send_json(200, resp)

            elif path == "/task-runs":
                resp = handle_task_runs(self.task_runs_path, limit)
                self._send_json(200, resp)

            elif path == "/mas-trace":
                resp = handle_mas_trace(self.mas_trace_path, limit)
                self._send_json(200, resp)

            # Memory endpoints
            elif path == "/memory":
                resp = handle_memory_get({}, self.memory_candidates_path,
                                         self.memory_proposals_path,
                                         self.memory_store_path, limit)
                self._send_json(200, resp)
            elif path == "/memory/candidates":
                resp = handle_memory_candidates_get(self.memory_candidates_path, limit)
                self._send_json(200, resp)
            elif path == "/memory/proposals":
                resp = handle_memory_proposals_get(self.memory_proposals_path, limit)
                self._send_json(200, resp)
            elif path == "/memory/reviews":
                resp = handle_memory_reviews_get(self.memory_reviews_path, limit)
                self._send_json(200, resp)
            elif path == "/memory/conflicts":
                resp = handle_memory_conflicts_get(self.memory_conflicts_path, limit)
                self._send_json(200, resp)
            elif path == "/memory/changes":
                resp = handle_memory_changes_get(self.memory_changes_path, limit)
                self._send_json(200, resp)
            elif path == "/memory/snapshots":
                resp = handle_memory_snapshots_get(self.memory_snapshots_path, limit)
                self._send_json(200, resp)

            # Research endpoints
            elif path == "/research/sources":
                resp = handle_research_sources_get(self.research_sources_path, limit)
                self._send_json(200, resp)
            elif path == "/research/packets":
                resp = handle_research_packets_get(self.research_packets_path, limit)
                self._send_json(200, resp)
            elif path == "/research/evidence":
                resp = handle_research_evidence_get(self.research_evidence_path, limit)
                self._send_json(200, resp)
            elif path == "/research/cognition-cards":
                resp = handle_research_cards_get(self.research_cards_path, limit)
                self._send_json(200, resp)
            elif path == "/research/handoffs":
                resp = handle_research_handoffs_get(limit)
                self._send_json(200, resp)

            # Growth endpoints
            elif path == "/growth/candidates":
                resp = handle_growth_candidates_get(self.growth_candidates_path, limit)
                self._send_json(200, resp)
            elif path == "/growth/goals":
                resp = handle_growth_goals_get(self.growth_goals_path, limit)
                self._send_json(200, resp)
            elif path == "/growth/capacity":
                resp = handle_growth_capacity_get(self.growth_capacity_path, limit)
                self._send_json(200, resp)
            elif path == "/growth/weekly-plans":
                resp = handle_growth_weekly_get(self.growth_weekly_path, limit)
                self._send_json(200, resp)
            elif path == "/growth/daily-tasks":
                resp = handle_growth_tasks_get(self.growth_tasks_path, limit)
                self._send_json(200, resp)
            elif path == "/growth/reviews":
                resp = handle_growth_reviews_get(self.growth_reviews_path, limit)
                self._send_json(200, resp)
            elif path == "/growth/adjustments":
                resp = handle_growth_adjustments_get(self.growth_adjustments_path, limit)
                self._send_json(200, resp)
            elif path == "/growth/handoffs":
                resp = handle_growth_handoffs_get(self.growth_handoffs_path, limit)
                self._send_json(200, resp)

            # Career endpoints
            elif path == "/career/assets":
                resp = handle_career_assets_get(self.career_assets_path, limit)
                self._send_json(200, resp)
            elif path == "/career/claims":
                resp = handle_career_claims_get(self.career_claims_path, limit)
                self._send_json(200, resp)
            elif path == "/career/jds":
                resp = handle_career_jds_get(self.career_jds_path, limit)
                self._send_json(200, resp)
            elif path == "/career/evaluations":
                resp = handle_career_evaluations_get(self.career_evaluations_path, limit)
                self._send_json(200, resp)
            elif path == "/career/applications":
                resp = handle_career_applications_get(self.career_applications_path, limit)
                self._send_json(200, resp)
            elif path == "/career/handoffs":
                resp = handle_career_handoffs_get(self.career_handoffs_path, limit)
                self._send_json(200, resp)

            # Readiness Center endpoints
            elif path == "/automation/workflows":
                resp = handle_automation_workflows_get(self.automation_workflows_path, limit)
                self._send_json(200, resp)
            elif path == "/automation/runs":
                resp = handle_automation_runs_get(self.automation_runs_path, limit)
                self._send_json(200, resp)
            elif path == "/skills/candidates":
                resp = handle_skill_candidates_get(self.skill_candidates_path, limit)
                self._send_json(200, resp)
            elif path == "/skills/reviews":
                resp = handle_skill_reviews_get(self.skill_reviews_path, limit)
                self._send_json(200, resp)
            elif path == "/knowledge/nodes":
                resp = handle_knowledge_nodes_get(self.knowledge_nodes_path, limit)
                self._send_json(200, resp)
            elif path == "/knowledge/edges":
                resp = handle_knowledge_edges_get(self.knowledge_edges_path, limit)
                self._send_json(200, resp)
            elif path == "/knowledge/boundaries":
                resp = handle_knowledge_boundaries_get(self.knowledge_boundaries_path, limit)
                self._send_json(200, resp)
            elif path == "/knowledge/state":
                resp = handle_knowledge_state_get(self.knowledge_state_path, limit)
                self._send_json(200, resp)
            elif path == "/model/routes":
                resp = handle_model_routes_get(self.model_routes_path, limit)
                self._send_json(200, resp)
            elif path == "/model/cost-events":
                resp = handle_cost_events_get(self.cost_events_path, limit)
                self._send_json(200, resp)
            elif path == "/mcp/profiles":
                resp = handle_mcp_profiles_get(self.mcp_profiles_path, limit)
                self._send_json(200, resp)
            elif path == "/mcp/tool-policies":
                resp = handle_tool_policies_get(self.tool_policies_path, limit)
                self._send_json(200, resp)

            else:
                self._send_json(404, build_response(False, error={
                    "code": "NOT_FOUND",
                    "message": f"route not found: {path}",
                }))
        except Exception:
            self._send_json(500, build_response(False, error={
                "code": "INTERNAL_ERROR",
                "message": traceback.format_exc()[:500],
            }))

    def do_POST(self):
        path = urlparse(self.path).path

        # Read body
        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            body_json = json.loads(body_raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, build_response(False, error={
                "code": "INVALID_JSON",
                "message": "request body must be valid JSON",
            }))
            return

        try:
            if path == "/command":
                command_text = body_json.get("command", "")
                resp = handle_command(command_text, self.gateway_path)
                self._send_json(200, resp)

            elif path == "/memory/candidates":
                resp = handle_memory_candidates_post(body_json, self.memory_candidate_script)
                self._send_json(200 if resp.get("ok") else 400, resp)

            elif path == "/memory/proposals":
                resp = handle_memory_proposals_post(body_json, self.memory_candidate_script)
                self._send_json(200 if resp.get("ok") else 400, resp)

            elif path == "/memory/store":
                resp = handle_memory_store_post(body_json, self.memory_store_script)
                self._send_json(200 if resp.get("ok") else 400, resp)

            elif path == "/memory/archive":
                resp = handle_memory_archive_post(body_json, self.memory_store_script)
                self._send_json(200, resp)

            elif path == "/memory/reviews":
                resp = handle_memory_review_post(body_json, self.memory_governance_script,
                                                 self.memory_candidates_path, self.memory_store_path,
                                                 self.memory_reviews_path, self.memory_conflicts_path,
                                                 self.memory_changes_path, self.memory_snapshots_path,
                                                 self.memory_snapshot_dir, self.memory_audit_path)
                self._send_json(_status_for(resp), resp)

            elif path == "/memory/conflicts":
                resp = handle_memory_conflict_post(body_json, self.memory_governance_script,
                                                   self.memory_candidates_path, self.memory_store_path,
                                                   self.memory_reviews_path, self.memory_conflicts_path,
                                                   self.memory_changes_path, self.memory_snapshots_path,
                                                   self.memory_snapshot_dir, self.memory_audit_path)
                self._send_json(_status_for(resp), resp)

            elif path == "/memory/changes":
                resp = handle_memory_change_post(body_json, self.memory_governance_script,
                                                 self.memory_candidates_path, self.memory_store_path,
                                                 self.memory_reviews_path, self.memory_conflicts_path,
                                                 self.memory_changes_path, self.memory_snapshots_path,
                                                 self.memory_snapshot_dir, self.memory_audit_path)
                self._send_json(_status_for(resp), resp)

            elif path == "/memory/snapshots":
                resp = handle_memory_snapshot_post(body_json, self.memory_governance_script,
                                                   self.memory_candidates_path, self.memory_store_path,
                                                   self.memory_reviews_path, self.memory_conflicts_path,
                                                   self.memory_changes_path, self.memory_snapshots_path,
                                                   self.memory_snapshot_dir, self.memory_audit_path)
                self._send_json(_status_for(resp), resp)

            # Research POST endpoints
            elif path == "/research/sources":
                resp = handle_research_sources_post(body_json, self.research_packet_script)
                self._send_json(200 if resp.get("ok") else 400, resp)
            elif path == "/research/sources/evaluate":
                resp = handle_research_evaluate_post(body_json, self.research_packet_script)
                self._send_json(200 if resp.get("ok") else 400, resp)
            elif path == "/research/packets":
                resp = handle_research_packets_post(body_json, self.research_packet_script)
                self._send_json(200 if resp.get("ok") else 400, resp)
            elif path == "/research/evidence":
                resp = handle_research_evidence_post(body_json, self.research_packet_script)
                self._send_json(200 if resp.get("ok") else 400, resp)
            elif path == "/research/packets/synthesize":
                resp = handle_research_synthesize_post(body_json, self.research_packet_script)
                self._send_json(200 if resp.get("ok") else 400, resp)
            elif path == "/research/cognition-cards":
                resp = handle_research_cards_post(body_json, self.cognition_card_script)
                self._send_json(200 if resp.get("ok") else 400, resp)
            elif path == "/research/handoffs":
                resp = handle_research_handoffs_post(body_json, self.research_packet_script)
                self._send_json(200 if resp.get("ok") else 400, resp)
            elif path == "/research/archive":
                resp = handle_research_archive_post(body_json, self.research_packet_script)
                self._send_json(200 if resp.get("ok") else 400, resp)

            # Growth POST endpoints
            elif path == "/growth/candidates":
                resp = handle_growth_candidates_post(body_json, self.growth_goal_script, self.growth_candidates_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/candidates/accept":
                resp = handle_growth_candidate_accept_post(body_json, self.growth_goal_script, self.growth_candidates_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/candidates/reject":
                resp = handle_growth_candidate_reject_post(body_json, self.growth_goal_script, self.growth_candidates_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/goals":
                resp = handle_growth_goals_post(body_json, self.growth_goal_script, self.growth_candidates_path, self.growth_goals_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/capacity":
                resp = handle_growth_capacity_post(body_json, self.growth_plan_script, self.growth_capacity_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/weekly-plans":
                resp = handle_growth_weekly_post(body_json, self.growth_plan_script, self.growth_weekly_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/daily-tasks":
                resp = handle_growth_tasks_post(body_json, self.growth_plan_script, self.growth_tasks_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/daily-tasks/status":
                resp = handle_growth_task_status_post(body_json, self.growth_plan_script, self.growth_tasks_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/reviews":
                resp = handle_growth_reviews_post(body_json, self.growth_review_script, self.growth_reviews_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/adjustments":
                resp = handle_growth_adjustments_post(body_json, self.growth_review_script, self.growth_adjustments_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/handoffs":
                resp = handle_growth_handoffs_post(body_json, self.growth_review_script, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/growth/archive":
                resp = handle_growth_archive_post(body_json, self.growth_goal_script, self.growth_goals_path, self.growth_audit_path)
                self._send_json(_status_for(resp), resp)

            # Career POST endpoints
            elif path == "/career/assets":
                resp = handle_career_assets_post(body_json, self.career_center_script,
                                                 self.career_assets_path, self.career_claims_path,
                                                 self.career_jds_path, self.career_evaluations_path,
                                                 self.career_applications_path, self.career_handoffs_path,
                                                 self.career_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/career/claims":
                resp = handle_career_claims_post(body_json, self.career_center_script,
                                                 self.career_assets_path, self.career_claims_path,
                                                 self.career_jds_path, self.career_evaluations_path,
                                                 self.career_applications_path, self.career_handoffs_path,
                                                 self.career_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/career/jds":
                resp = handle_career_jds_post(body_json, self.career_center_script,
                                              self.career_assets_path, self.career_claims_path,
                                              self.career_jds_path, self.career_evaluations_path,
                                              self.career_applications_path, self.career_handoffs_path,
                                              self.career_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/career/evaluations":
                resp = handle_career_evaluations_post(body_json, self.career_center_script,
                                                      self.career_assets_path, self.career_claims_path,
                                                      self.career_jds_path, self.career_evaluations_path,
                                                      self.career_applications_path, self.career_handoffs_path,
                                                      self.career_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/career/applications":
                resp = handle_career_applications_post(body_json, self.career_center_script,
                                                       self.career_assets_path, self.career_claims_path,
                                                       self.career_jds_path, self.career_evaluations_path,
                                                       self.career_applications_path, self.career_handoffs_path,
                                                       self.career_audit_path)
                self._send_json(_status_for(resp), resp)
            elif path == "/career/handoffs":
                resp = handle_career_handoffs_post(body_json, self.career_center_script,
                                                   self.career_assets_path, self.career_claims_path,
                                                   self.career_jds_path, self.career_evaluations_path,
                                                   self.career_applications_path, self.career_handoffs_path,
                                                   self.career_audit_path)
                self._send_json(_status_for(resp), resp)

            # Readiness Center POST endpoints
            elif path == "/automation/workflows":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_automation_workflows_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/automation/runs":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_automation_runs_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/skills/candidates":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_skill_candidates_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/skills/reviews":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_skill_reviews_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/knowledge/nodes":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_knowledge_nodes_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/knowledge/edges":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_knowledge_edges_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/knowledge/boundaries":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_knowledge_boundaries_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/knowledge/state":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_knowledge_state_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/model/routes":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_model_routes_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/model/cost-events":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_cost_events_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/mcp/profiles":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_mcp_profiles_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)
            elif path == "/mcp/tool-policies":
                paths = (self.automation_workflows_path, self.automation_runs_path, self.skill_candidates_path,
                         self.skill_reviews_path, self.knowledge_nodes_path, self.knowledge_edges_path,
                         self.knowledge_boundaries_path, self.knowledge_state_path, self.model_routes_path,
                         self.cost_events_path, self.mcp_profiles_path, self.tool_policies_path,
                         self.readiness_audit_path)
                resp = handle_tool_policies_post(body_json, self.readiness_center_script, paths)
                self._send_json(_status_for(resp), resp)

            else:
                self._send_json(404, build_response(False, error={
                    "code": "NOT_FOUND",
                    "message": f"POST route not found: {path}",
                }))
        except Exception:
            self._send_json(500, build_response(False, error={
                "code": "INTERNAL_ERROR",
                "message": traceback.format_exc()[:500],
            }))

    def log_message(self, format, *args):
        """Suppress default stderr logging in tests."""
        pass


def create_server(host, port, handler_class=OnePalHandler):
    """Create and return an HTTPServer instance."""
    server = HTTPServer((host, port), handler_class)
    return server


def main():
    parser = argparse.ArgumentParser(description="OnePal Minimum API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=18790, help="Port to bind")
    parser.add_argument("--health-path", default=None, help="Override health_status.json path")
    parser.add_argument("--tasks-path", default=None, help="Override tasks.jsonl path")
    parser.add_argument("--trees-path", default=None, help="Override task_trees.jsonl path")
    parser.add_argument("--task-runs-path", default=None, help="Override task_runs.jsonl path")
    parser.add_argument("--mas-trace-path", default=None, help="Override mas_trace.jsonl path")
    parser.add_argument("--gateway-path", default=None, help="Override command_gateway.py path")
    args = parser.parse_args()

    host = args.host.strip().lower()

    # Reject 0.0.0.0
    if host == "0.0.0.0":
        print(json.dumps({
            "error": "Binding to 0.0.0.0 is forbidden. Use 127.0.0.1 or localhost."
        }, ensure_ascii=False))
        sys.exit(1)

    if host not in ALLOWED_HOSTS:
        print(json.dumps({
            "error": f"Host '{host}' is not allowed. Use 127.0.0.1 or localhost."
        }, ensure_ascii=False))
        sys.exit(1)

    # Build handler class with path overrides
    class ConfiguredHandler(OnePalHandler):
        health_path = Path(args.health_path) if args.health_path else HEALTH_PATH
        tasks_path = Path(args.tasks_path) if args.tasks_path else TASKS_PATH
        trees_path = Path(args.trees_path) if args.trees_path else TREES_PATH
        task_runs_path = Path(args.task_runs_path) if args.task_runs_path else TASK_RUNS_PATH
        mas_trace_path = Path(args.mas_trace_path) if args.mas_trace_path else MAS_TRACE_PATH
        gateway_path = Path(args.gateway_path) if args.gateway_path else COMMAND_GATEWAY

    server = create_server(host, args.port, ConfiguredHandler)
    print(f"OnePal API Server listening on http://{host}:{args.port}")
    print("Endpoints: GET /health /tasks /task-trees /task-runs /mas-trace /memory/* /research/* /growth/*  POST /command")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
