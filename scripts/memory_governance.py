#!/usr/bin/env python3
"""OnePal Memory Governance Manager - Task 14-B.

Creates quality reviews, conflict records, memory change requests, and memory
snapshots. This script never writes approved memory entries to the memory store;
store writes remain controlled by memory_store.py and approved proposals.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CANDIDATES = ROOT / "memory" / "candidates" / "memory_candidates.jsonl"
DEFAULT_STORE = ROOT / "memory" / "store" / "memory_store.jsonl"
DEFAULT_REVIEWS = ROOT / "memory" / "reviews" / "memory_quality_reviews.jsonl"
DEFAULT_CONFLICTS = ROOT / "memory" / "conflicts" / "memory_conflicts.jsonl"
DEFAULT_CHANGES = ROOT / "memory" / "changes" / "memory_change_requests.jsonl"
DEFAULT_SNAPSHOTS = ROOT / "memory" / "snapshots" / "memory_snapshots.jsonl"
DEFAULT_SNAPSHOT_DIR = ROOT / "memory" / "snapshots" / "files"
DEFAULT_AUDIT = ROOT / "logs" / "memory_audit.jsonl"

SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{10,}",
    r"-----BEGIN",
    r"ghp_[a-zA-Z0-9]{20,}",
    r"(?:api[_-]?key)\s*[:=]\s*\S{10,}",
    r"(?:password|passwd)\s*[:=]\s*\S{8,}",
    r"(?:token)\s*[:=]\s*\S{10,}",
    r"(?:secret)\s*[:=]\s*\S{8,}",
]

SCORE_KEYS = [
    "clarity",
    "specificity",
    "evidence_strength",
    "stability",
    "actionability",
    "non_sensitivity",
    "non_duplicate",
    "scope_fit",
]

VALID_CHANGE_TYPES = {"create", "update", "merge", "supersede", "archive", "redact", "forget", "delete"}


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


def write_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def audit(action, detail, audit_path, **refs):
    entry = {
        "audit_id": f"audit_{uuid4().hex[:12]}",
        "action": action,
        "detail": detail[:300],
        "timestamp": now_iso(),
    }
    entry.update({k: v for k, v in refs.items() if v})
    append_jsonl(audit_path, entry)
    return entry


def fail(message, status="error"):
    print(json.dumps({"status": status, "error": message}, ensure_ascii=False))
    sys.exit(1)


def detect_secret(text):
    return any(re.search(pat, text or "", re.IGNORECASE) for pat in SECRET_PATTERNS)


def normalize(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def clamp_score(value):
    return max(0.0, min(1.0, float(value)))


def find_record(records, key, value):
    for record in records:
        if record.get(key) == value:
            return record
    return None


def target_content(target):
    return target.get("content") or target.get("content_summary") or target.get("proposed_memory_text") or ""


def load_target(args, candidates_path, store_path):
    if args.target_type == "candidate":
        target = find_record(load_jsonl(candidates_path), "candidate_id", args.target_ref)
    elif args.target_type == "entry":
        target = find_record(load_jsonl(store_path), "memory_id", args.target_ref)
    else:
        fail("target_type must be candidate or entry")
    if target is None:
        fail(f"{args.target_type} '{args.target_ref}' not found", "not_found")
    return target


def compute_scores(target, existing_refs=None):
    content = target_content(target)
    word_count = len(content.split())
    secret = detect_secret(content)
    has_source = bool(target.get("source_candidate_id") or target.get("source_agent") or target.get("provenance"))
    scores = {
        "clarity": 0.9 if content.strip() else 0.0,
        "specificity": 0.85 if word_count >= 6 else 0.55,
        "evidence_strength": 0.85 if has_source else 0.55,
        "stability": 0.8,
        "actionability": 0.75 if word_count >= 4 else 0.45,
        "non_sensitivity": 0.0 if secret else 1.0,
        "non_duplicate": 0.45 if existing_refs else 1.0,
        "scope_fit": 0.8,
    }
    return {key: clamp_score(scores[key]) for key in SCORE_KEYS}


def review_create(args, candidates_path, store_path, reviews_path, audit_path):
    target = load_target(args, candidates_path, store_path)
    scores = compute_scores(target)
    overall = round(sum(scores.values()) / len(scores), 3)
    issues = []
    if scores["non_sensitivity"] == 0:
        issues.append("secret_like_content")
    if scores["specificity"] < 0.7:
        issues.append("low_specificity")
    if scores["evidence_strength"] < 0.7:
        issues.append("weak_provenance")

    sensitivity = target.get("sensitivity", "internal")
    source_type = target.get("source_type") or target.get("provenance", {}).get("origin_type")
    requires_confirmation = source_type in {"agent_inferred", "external_source"} or sensitivity in {"sensitive", "forbidden"}
    if scores["non_sensitivity"] == 0:
        recommendation = "reject_candidate" if args.target_type == "candidate" else "redact"
        requires_confirmation = True
    elif overall >= 0.78 and not requires_confirmation:
        recommendation = "approve"
    elif overall >= 0.62:
        recommendation = "request_user_confirmation" if requires_confirmation else "approve_with_edit"
        requires_confirmation = True if recommendation == "request_user_confirmation" else requires_confirmation
    else:
        recommendation = "reject_candidate" if args.target_type == "candidate" else "archive"

    review = {
        "memory_quality_review_id": f"memqr_{uuid4().hex[:12]}",
        "target_type": args.target_type,
        "target_ref": args.target_ref,
        "reviewer_agent": args.reviewer_agent,
        "created_at": now_iso(),
        "scores": scores,
        "overall_score": overall,
        "issues": issues,
        "recommendation": recommendation,
        "requires_user_confirmation": requires_confirmation,
        "suggested_scope": args.suggested_scope,
        "suggested_retention": args.suggested_retention,
        "review_notes": args.review_notes,
    }
    append_jsonl(reviews_path, review)
    audit("memory_quality_review_created", f"review={review['memory_quality_review_id']}",
          audit_path, quality_review_id=review["memory_quality_review_id"], target_ref=args.target_ref)
    print(json.dumps({"status": "created", "review": review}, indent=2, ensure_ascii=False))


def conflict_detect(args, candidates_path, store_path, conflicts_path, audit_path):
    target = load_target(args, candidates_path, store_path)
    content = normalize(target_content(target))
    if not content:
        fail("target content is empty")

    matches = []
    for memory in load_jsonl(store_path):
        mid = memory.get("memory_id")
        existing = normalize(memory.get("content", ""))
        if not mid or not existing:
            continue
        if existing == content or existing in content or content in existing:
            matches.append(mid)

    if not matches:
        audit("memory_conflict_none", f"target={args.target_ref}", audit_path, target_ref=args.target_ref)
        print(json.dumps({"status": "no_conflict", "target_ref": args.target_ref, "conflicts": []}, ensure_ascii=False))
        return

    conflict = {
        "memory_conflict_id": f"memconf_{uuid4().hex[:12]}",
        "conflict_type": "duplicate",
        "severity": "low" if len(matches) == 1 else "medium",
        "status": "open",
        "summary": f"Target {args.target_ref} appears to duplicate existing memory.",
        "detected_at": now_iso(),
        "detected_by": args.detected_by,
        "candidate_ref": args.target_ref if args.target_type == "candidate" else None,
        "entry_ref": args.target_ref if args.target_type == "entry" else None,
        "existing_memory_refs": matches[:10],
        "evidence_refs": [args.target_ref] + matches[:10],
        "recommended_resolution": "merge",
        "resolution": {
            "strategy": "unresolved",
            "requires_user_approval": True,
            "decision_ref": None,
            "resolved_by": None,
            "resolved_at": None,
            "resolution_note": None,
        },
        "audit_ref": None,
    }
    append_jsonl(conflicts_path, conflict)
    audit("memory_conflict_detected", f"conflict={conflict['memory_conflict_id']}",
          audit_path, conflict_id=conflict["memory_conflict_id"], target_ref=args.target_ref)
    print(json.dumps({"status": "created", "conflict": conflict}, indent=2, ensure_ascii=False))


def change_create(args, candidates_path, store_path, changes_path, audit_path):
    if args.change_type not in VALID_CHANGE_TYPES:
        fail(f"invalid change_type: {args.change_type}")
    target_refs = [item.strip() for item in args.target_refs.split(",") if item.strip()]
    if not target_refs:
        fail("target_refs required")

    proposed_entry = None
    if args.change_type == "create" and args.source_candidate_id:
        candidate = find_record(load_jsonl(candidates_path), "candidate_id", args.source_candidate_id)
        if candidate is None:
            fail(f"candidate '{args.source_candidate_id}' not found", "not_found")
        proposed_entry = {
            "memory_type": candidate.get("memory_type", "other"),
            "content": target_content(candidate),
            "source_candidate_ref": candidate.get("candidate_id"),
            "sensitivity": candidate.get("sensitivity", "internal"),
            "status": "draft",
        }
    elif args.source_memory_id:
        memory = find_record(load_jsonl(store_path), "memory_id", args.source_memory_id)
        if memory is None:
            fail(f"memory '{args.source_memory_id}' not found", "not_found")
        proposed_entry = dict(memory)

    risk = "R3" if args.change_type in {"create", "update", "merge", "supersede", "redact", "forget", "delete"} else "R2"
    change = {
        "memory_change_request_id": f"memchg_{uuid4().hex[:12]}",
        "change_type": args.change_type,
        "requested_by": args.requested_by,
        "risk_level": risk,
        "requires_user_approval": True,
        "status": "pending_review",
        "reason": args.reason,
        "target_refs": target_refs,
        "proposed_entry": proposed_entry,
        "merge_sources": [item.strip() for item in args.merge_sources.split(",") if item.strip()],
        "approval_ref": None,
        "audit_ref": None,
        "rollback_plan": {
            "available": True,
            "strategy": args.rollback_strategy,
            "snapshot_ref": args.snapshot_ref,
        },
        "created_at": now_iso(),
        "updated_at": None,
    }
    append_jsonl(changes_path, change)
    audit("memory_change_request_created", f"change={change['memory_change_request_id']}",
          audit_path, change_request_id=change["memory_change_request_id"])
    print(json.dumps({"status": "created", "change_request": change}, indent=2, ensure_ascii=False))


def snapshot_create(args, store_path, snapshots_path, snapshot_dir, audit_path):
    entries = load_jsonl(store_path)
    payload = {
        "created_at": now_iso(),
        "reason": args.reason,
        "entries": entries,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    sid = f"memsnap_{uuid4().hex[:12]}"
    storage_path = snapshot_dir / f"{sid}.json"
    write_json(storage_path, payload)

    try:
        safe_storage_path = str(storage_path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        safe_storage_path = str(storage_path)

    snapshot = {
        "memory_snapshot_id": sid,
        "created_at": payload["created_at"],
        "created_by": args.created_by,
        "reason": args.reason,
        "storage_path": safe_storage_path,
        "content_hash": digest,
        "included_scopes": [item.strip() for item in args.included_scopes.split(",") if item.strip()],
        "entry_count": len(entries),
        "status": "created",
        "restore_available": True,
        "notes": args.notes,
    }
    append_jsonl(snapshots_path, snapshot)
    audit("memory_snapshot_created", f"snapshot={sid}", audit_path, snapshot_id=sid)
    print(json.dumps({"status": "created", "snapshot": snapshot}, indent=2, ensure_ascii=False))


def list_records(args):
    paths = {
        "reviews": Path(args.reviews_log) if args.reviews_log else DEFAULT_REVIEWS,
        "conflicts": Path(args.conflicts_log) if args.conflicts_log else DEFAULT_CONFLICTS,
        "changes": Path(args.changes_log) if args.changes_log else DEFAULT_CHANGES,
        "snapshots": Path(args.snapshots_log) if args.snapshots_log else DEFAULT_SNAPSHOTS,
    }
    if args.record_type not in paths:
        fail("record_type must be reviews, conflicts, changes, or snapshots")
    rows = load_jsonl(paths[args.record_type])
    limit = min(int(args.limit or 20), 100)
    print(json.dumps({args.record_type: rows[-limit:], "total": len(rows), "shown": min(limit, len(rows))},
                     indent=2, ensure_ascii=False))


def add_common_paths(parser):
    parser.add_argument("--candidates-log", default=None)
    parser.add_argument("--store-log", default=None)
    parser.add_argument("--reviews-log", default=None)
    parser.add_argument("--conflicts-log", default=None)
    parser.add_argument("--changes-log", default=None)
    parser.add_argument("--snapshots-log", default=None)
    parser.add_argument("--snapshot-dir", default=None)
    parser.add_argument("--audit-log", default=None)


def main():
    parser = argparse.ArgumentParser(description="OnePal Memory Governance Manager")
    sub = parser.add_subparsers(dest="cmd")

    review = sub.add_parser("review-create", help="Create memory quality review")
    review.add_argument("--target-type", required=True, choices=["candidate", "entry"])
    review.add_argument("--target-ref", required=True)
    review.add_argument("--reviewer-agent", default="Memory Curator")
    review.add_argument("--suggested-scope", default="project")
    review.add_argument("--suggested-retention", default="long")
    review.add_argument("--review-notes", default=None)
    add_common_paths(review)

    conflict = sub.add_parser("conflict-detect", help="Detect duplicate memory conflicts")
    conflict.add_argument("--target-type", required=True, choices=["candidate", "entry"])
    conflict.add_argument("--target-ref", required=True)
    conflict.add_argument("--detected-by", default="Memory Curator")
    add_common_paths(conflict)

    change = sub.add_parser("change-create", help="Create memory change request")
    change.add_argument("--change-type", required=True)
    change.add_argument("--target-refs", required=True)
    change.add_argument("--reason", required=True)
    change.add_argument("--requested-by", default="Memory Curator")
    change.add_argument("--source-candidate-id", default=None)
    change.add_argument("--source-memory-id", default=None)
    change.add_argument("--merge-sources", default="")
    change.add_argument("--snapshot-ref", default=None)
    change.add_argument("--rollback-strategy", default="restore previous snapshot or leave request unapplied")
    add_common_paths(change)

    snapshot = sub.add_parser("snapshot-create", help="Create memory store snapshot")
    snapshot.add_argument("--reason", required=True)
    snapshot.add_argument("--created-by", default="Memory Curator")
    snapshot.add_argument("--included-scopes", default="project")
    snapshot.add_argument("--notes", default=None)
    add_common_paths(snapshot)

    list_cmd = sub.add_parser("list", help="List governance records")
    list_cmd.add_argument("--record-type", required=True, choices=["reviews", "conflicts", "changes", "snapshots"])
    list_cmd.add_argument("--limit", type=int, default=20)
    add_common_paths(list_cmd)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    candidates_path = Path(args.candidates_log) if getattr(args, "candidates_log", None) else DEFAULT_CANDIDATES
    store_path = Path(args.store_log) if getattr(args, "store_log", None) else DEFAULT_STORE
    reviews_path = Path(args.reviews_log) if getattr(args, "reviews_log", None) else DEFAULT_REVIEWS
    conflicts_path = Path(args.conflicts_log) if getattr(args, "conflicts_log", None) else DEFAULT_CONFLICTS
    changes_path = Path(args.changes_log) if getattr(args, "changes_log", None) else DEFAULT_CHANGES
    snapshots_path = Path(args.snapshots_log) if getattr(args, "snapshots_log", None) else DEFAULT_SNAPSHOTS
    snapshot_dir = Path(args.snapshot_dir) if getattr(args, "snapshot_dir", None) else DEFAULT_SNAPSHOT_DIR
    audit_path = Path(args.audit_log) if getattr(args, "audit_log", None) else DEFAULT_AUDIT

    if args.cmd == "review-create":
        review_create(args, candidates_path, store_path, reviews_path, audit_path)
    elif args.cmd == "conflict-detect":
        conflict_detect(args, candidates_path, store_path, conflicts_path, audit_path)
    elif args.cmd == "change-create":
        change_create(args, candidates_path, store_path, changes_path, audit_path)
    elif args.cmd == "snapshot-create":
        snapshot_create(args, store_path, snapshots_path, snapshot_dir, audit_path)
    elif args.cmd == "list":
        list_records(args)


if __name__ == "__main__":
    main()
