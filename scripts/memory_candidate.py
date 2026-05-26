#!/usr/bin/env python3
"""OnePal Memory Candidate Manager - Task 08-B

Creates, validates, deduplicates, and promotes memory candidates.
Detects secrets and forbidden content.

Usage:
    py scripts/memory_candidate.py create --source-type manual --source-agent user --memory-type project_decision --content "..."
    py scripts/memory_candidate.py validate --candidate-id memcand_xxx
    py scripts/memory_candidate.py propose --candidate-id memcand_xxx
    py scripts/memory_candidate.py list --limit 20
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CANDIDATES_LOG = PROJECT_ROOT / "memory" / "candidates" / "memory_candidates.jsonl"
DEFAULT_PROPOSALS_LOG = PROJECT_ROOT / "memory" / "proposals" / "memory_proposals.jsonl"
DEFAULT_AUDIT_LOG = PROJECT_ROOT / "logs" / "memory_audit.jsonl"

VALID_MEMORY_TYPES = {
    "user_preference", "project_decision", "system_rule", "project_state",
    "feedback_pattern", "workflow_preference", "agent_instruction",
    "career_preference", "learning_preference", "temporary_note",
}
VALID_SENSITIVITY = {"public", "internal", "personal", "sensitive", "forbidden"}
FORBIDDEN_SENSITIVITY = {"forbidden"}

# Secret detection patterns
SECRET_PATTERNS = [
    r'sk-[a-zA-Z0-9]{10,}',           # OpenAI keys
    r'-----BEGIN\s.*PRIVATE\sKEY',    # Private keys
    r'ghp_[a-zA-Z0-9]{20,}',           # GitHub tokens
    r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}',  # JWT
    r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
    r'(?:api[_-]?key|API[_-]?KEY)\s*[:=]\s*\S{10,}',  # API key assignments
    r'(?:password|passwd)\s*[:=]\s*\S{8,}',  # Passwords
    r'(?:token|TOKEN)\s*[:=]\s*\S{10,}',  # Token assignments
    r'(?:secret|SECRET)\s*[:=]\s*\S{8,}',  # Secret assignments
]


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


def compute_dedupe_key(memory_type, content, source):
    raw = f"{memory_type}|{content.strip()[:100]}|{source}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def detect_secrets(content):
    """Return list of matched pattern names (no content leaked)."""
    hits = []
    for pat in SECRET_PATTERNS:
        if re.search(pat, content, re.IGNORECASE):
            hits.append(pat[:40])
    return hits


def audit(action, detail, audit_path, candidate_id=None, proposal_id=None):
    entry = {
        "audit_id": f"audit_{uuid4().hex[:12]}",
        "action": action,
        "candidate_id": candidate_id,
        "proposal_id": proposal_id,
        "detail": detail[:300],
        "timestamp": now_iso(),
    }
    append_jsonl(audit_path, entry)
    return entry


def create_candidate(args, candidates_path, audit_path):
    content = (args.content or "").strip()
    if not content:
        print(json.dumps({"error": "content is required"}, ensure_ascii=False))
        sys.exit(1)

    mem_type = args.memory_type
    if mem_type not in VALID_MEMORY_TYPES:
        print(json.dumps({"error": f"invalid memory_type: {mem_type}"}, ensure_ascii=False))
        sys.exit(1)

    sensitivity = args.sensitivity
    if sensitivity not in VALID_SENSITIVITY:
        print(json.dumps({"error": f"invalid sensitivity: {sensitivity}"}, ensure_ascii=False))
        sys.exit(1)

    # Secret detection
    secrets = detect_secrets(content)
    if secrets:
        audit("candidate_rejected_secret", f"secrets detected in candidate", audit_path)
        print(json.dumps({
            "status": "rejected",
            "reason": "secret_or_sensitive_content_detected",
            "error": "Content contains patterns matching secrets. Rejected.",
        }, ensure_ascii=False))
        sys.exit(1)

    # Forbidden sensitivity
    if sensitivity in FORBIDDEN_SENSITIVITY:
        audit("candidate_rejected_forbidden", f"sensitivity={sensitivity}", audit_path)
        print(json.dumps({
            "status": "rejected",
            "reason": "forbidden_sensitivity",
            "error": f"Sensitivity '{sensitivity}' is forbidden.",
        }, ensure_ascii=False))
        sys.exit(1)

    source_type = args.source_type
    requires_user_confirmation = source_type in ("agent_inferred", "external_source")

    candidate = {
        "candidate_id": f"memcand_{uuid4().hex[:12]}",
        "memory_type": mem_type,
        "content": content,
        "content_summary": content[:200],
        "source_type": source_type,
        "source_agent": args.source_agent,
        "confidence": max(0.0, min(1.0, float(args.confidence))),
        "sensitivity": sensitivity,
        "requires_user_confirmation": requires_user_confirmation,
        "dedupe_key": compute_dedupe_key(mem_type, content, args.source_agent),
        "status": "captured",
        "created_at": now_iso(),
        "updated_at": None,
    }
    append_jsonl(candidates_path, candidate)
    audit("candidate_created", f"candidate_id={candidate['candidate_id']}", audit_path, candidate_id=candidate["candidate_id"])

    print(json.dumps({"status": "created", "candidate": candidate}, indent=2, ensure_ascii=False))
    return candidate


def validate_candidate(args, candidates_path, audit_path):
    cid = args.candidate_id
    candidates = load_jsonl(candidates_path)
    target = None
    for c in candidates:
        if c.get("candidate_id") == cid:
            target = c
            break

    if target is None:
        print(json.dumps({"status": "not_found", "candidate_id": cid}, ensure_ascii=False))
        sys.exit(1)

    issues = []
    if not target.get("content", "").strip():
        issues.append("empty_content")
    if target.get("memory_type") not in VALID_MEMORY_TYPES:
        issues.append("invalid_memory_type")
    if target.get("sensitivity") not in VALID_SENSITIVITY:
        issues.append("invalid_sensitivity")

    secrets = detect_secrets(target.get("content", ""))
    if secrets:
        issues.append("secret_content_detected")

    if target.get("sensitivity") in FORBIDDEN_SENSITIVITY:
        issues.append("forbidden_sensitivity")

    result = {
        "candidate_id": cid,
        "valid": len(issues) == 0,
        "issues": issues,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def propose_candidate(args, candidates_path, proposals_path, audit_path):
    cid = args.candidate_id
    candidates = load_jsonl(candidates_path)
    target = None
    for c in candidates:
        if c.get("candidate_id") == cid:
            target = c
            break

    if target is None:
        print(json.dumps({"status": "not_found", "candidate_id": cid}, ensure_ascii=False))
        sys.exit(1)

    # Check status — only captured/draft can be proposed
    if target.get("status") not in ("captured", "draft", "pending_review"):
        print(json.dumps({"status": "error", "reason": f"candidate status is '{target.get('status')}', not proposable"}, ensure_ascii=False))
        sys.exit(1)

    # Secret re-check
    secrets = detect_secrets(target.get("content", ""))
    if secrets:
        audit("proposal_rejected_secret", f"candidate={cid}", audit_path, candidate_id=cid)
        update_candidate_status(candidates_path, cid, "rejected")
        print(json.dumps({"status": "rejected", "reason": "secret_content"}, ensure_ascii=False))
        sys.exit(1)

    # Forbidden re-check
    if target.get("sensitivity") in FORBIDDEN_SENSITIVITY:
        audit("proposal_rejected_forbidden", f"candidate={cid}", audit_path, candidate_id=cid)
        update_candidate_status(candidates_path, cid, "rejected")
        print(json.dumps({"status": "rejected", "reason": "forbidden_sensitivity"}, ensure_ascii=False))
        sys.exit(1)

    # Dedupe check — any existing candidate with same key
    dkey = target.get("dedupe_key", "")
    existing = [c for c in candidates
                if c.get("dedupe_key") == dkey
                and c.get("candidate_id") != cid]
    if existing:
        print(json.dumps({"status": "deduped", "existing_candidate_id": existing[0].get("candidate_id"),
                          "reason": "duplicate candidate already exists"}, ensure_ascii=False))
        sys.exit(1)

    proposal = {
        "proposal_id": f"memprop_{uuid4().hex[:12]}",
        "candidate_id": cid,
        "proposal_type": "memory_write",
        "proposed_memory_text": target.get("content", ""),
        "memory_type": target.get("memory_type"),
        "reason": args.reason or f"Memory proposal for candidate {cid}",
        "source_summary": f"source: {target.get('source_agent')}, type: {target.get('source_type')}",
        "risk_level": "R1",
        "sensitivity": target.get("sensitivity"),
        "requires_approval": True,
        "requires_user_confirmation": target.get("requires_user_confirmation", False),
        "created_at": now_iso(),
        "status": "pending_review",
    }
    append_jsonl(proposals_path, proposal)
    update_candidate_status(candidates_path, cid, "proposed")
    audit("proposal_created", f"proposal_id={proposal['proposal_id']}", audit_path,
          candidate_id=cid, proposal_id=proposal["proposal_id"])

    print(json.dumps({"status": "proposed", "proposal": proposal, "candidate_id": cid}, indent=2, ensure_ascii=False))
    return proposal


def update_candidate_status(candidates_path, cid, new_status):
    candidates = load_jsonl(candidates_path)
    for i, c in enumerate(candidates):
        if c.get("candidate_id") == cid:
            candidates[i]["status"] = new_status
            candidates[i]["updated_at"] = now_iso()
            break
    write_jsonl(candidates_path, candidates)


def list_candidates(args, candidates_path):
    candidates = load_jsonl(candidates_path)
    limit = min(int(args.limit or 20), 100)
    latest = candidates[-limit:]
    print(json.dumps({"candidates": latest, "total": len(candidates), "shown": len(latest)}, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="OnePal Memory Candidate Manager")
    sub = parser.add_subparsers(dest="command")

    # create
    p_create = sub.add_parser("create", help="Create a memory candidate")
    p_create.add_argument("--source-type", default="manual", choices=["user_direct", "user_confirmed", "agent_inferred", "external_source", "system_generated"])
    p_create.add_argument("--source-agent", default="user", help="Agent or source")
    p_create.add_argument("--memory-type", default="project_decision", help="Memory type")
    p_create.add_argument("--content", required=True, help="Memory content text")
    p_create.add_argument("--confidence", default=0.8, type=float)
    p_create.add_argument("--sensitivity", default="personal", help="Sensitivity level")
    p_create.add_argument("--candidates-log", default=None)

    # validate
    p_val = sub.add_parser("validate")
    p_val.add_argument("--candidate-id", required=True)
    p_val.add_argument("--candidates-log", default=None)

    # propose
    p_prop = sub.add_parser("propose")
    p_prop.add_argument("--candidate-id", required=True)
    p_prop.add_argument("--reason", default=None)
    p_prop.add_argument("--candidates-log", default=None)
    p_prop.add_argument("--proposals-log", default=None)

    # list
    p_list = sub.add_parser("list")
    p_list.add_argument("--limit", default=20, type=int)
    p_list.add_argument("--candidates-log", default=None)

    # Global path override
    for p in [p_create, p_val, p_prop, p_list]:
        p.add_argument("--audit-log", default=None)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    candidates_path = Path(vars(args).get("candidates_log")) if vars(args).get("candidates_log") else DEFAULT_CANDIDATES_LOG
    proposals_path = Path(vars(args).get("proposals_log")) if vars(args).get("proposals_log") else DEFAULT_PROPOSALS_LOG
    audit_path = Path(vars(args).get("audit_log")) if vars(args).get("audit_log") else DEFAULT_AUDIT_LOG

    if args.command == "create":
        create_candidate(args, candidates_path, audit_path)
    elif args.command == "validate":
        validate_candidate(args, candidates_path, audit_path)
    elif args.command == "propose":
        propose_candidate(args, candidates_path, proposals_path, audit_path)
    elif args.command == "list":
        list_candidates(args, candidates_path)


if __name__ == "__main__":
    main()
