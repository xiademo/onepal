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
MEMORY_CANDIDATES_PATH = PROJECT_ROOT / "memory" / "candidates" / "memory_candidates.jsonl"
MEMORY_PROPOSALS_PATH = PROJECT_ROOT / "memory" / "proposals" / "memory_proposals.jsonl"
MEMORY_STORE_PATH = PROJECT_ROOT / "memory" / "store" / "memory_store.jsonl"
RESEARCH_SOURCES_PATH = PROJECT_ROOT / "research" / "sources" / "research_sources.jsonl"
RESEARCH_PACKETS_PATH = PROJECT_ROOT / "research" / "packets" / "research_packets.jsonl"
RESEARCH_EVIDENCE_PATH = PROJECT_ROOT / "research" / "evidence" / "evidence_packs.jsonl"
RESEARCH_CARDS_PATH = PROJECT_ROOT / "research" / "cognition" / "cognition_cards.jsonl"
RESEARCH_HANDOFFS_DIR = PROJECT_ROOT / "research" / "handoffs"
RESEARCH_PACKET_SCRIPT = PROJECT_ROOT / "scripts" / "research_packet.py"
COGNITION_CARD_SCRIPT = PROJECT_ROOT / "scripts" / "cognition_card.py"

MAX_LIMIT = 100
MAX_COMMAND_LENGTH = 2000
MAX_MEMORY_CONTENT = 4000

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
    memory_candidates_path = MEMORY_CANDIDATES_PATH
    memory_proposals_path = MEMORY_PROPOSALS_PATH
    memory_store_path = MEMORY_STORE_PATH
    research_sources_path = RESEARCH_SOURCES_PATH
    research_packets_path = RESEARCH_PACKETS_PATH
    research_evidence_path = RESEARCH_EVIDENCE_PATH
    research_cards_path = RESEARCH_CARDS_PATH
    research_packet_script = RESEARCH_PACKET_SCRIPT
    cognition_card_script = COGNITION_CARD_SCRIPT

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
    print("Endpoints: GET /health /tasks /task-trees /task-runs /mas-trace  POST /command")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
