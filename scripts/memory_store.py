#!/usr/bin/env python3
"""OnePal Memory Store Manager - Task 08-B

Writes, lists, archives, and supersedes memory store entries.
Only approved proposals can enter the store.

Usage:
    py scripts/memory_store.py store --proposal-id memprop_xxx
    py scripts/memory_store.py list --status active --limit 20
    py scripts/memory_store.py archive --memory-id mem_xxx --reason "..."
    py scripts/memory_store.py supersede --memory-id mem_xxx --new-memory-id mem_yyy
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_STORE_LOG = PROJECT_ROOT / "memory" / "store" / "memory_store.jsonl"
DEFAULT_ARCHIVE_LOG = PROJECT_ROOT / "memory" / "archive" / "memory_archive.jsonl"
DEFAULT_PROPOSALS_LOG = PROJECT_ROOT / "memory" / "proposals" / "memory_proposals.jsonl"
DEFAULT_AUDIT_LOG = PROJECT_ROOT / "logs" / "memory_audit.jsonl"


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


def audit(action, detail, audit_path, memory_id=None, proposal_id=None, candidate_id=None):
    entry = {
        "audit_id": f"audit_{uuid4().hex[:12]}",
        "action": action,
        "memory_id": memory_id,
        "proposal_id": proposal_id,
        "candidate_id": candidate_id,
        "detail": detail[:300],
        "timestamp": now_iso(),
    }
    append_jsonl(audit_path, entry)


def store_memory(args, store_path, proposals_path, audit_path):
    pid = args.proposal_id
    proposals = load_jsonl(proposals_path)
    target = None
    for p in proposals:
        if p.get("proposal_id") == pid:
            target = p
            break

    if target is None:
        print(json.dumps({"status": "error", "reason": f"proposal '{pid}' not found"}, ensure_ascii=False))
        sys.exit(1)

    pstatus = target.get("status", "")
    if pstatus not in ("approved",):
        audit("store_rejected_unapproved", f"proposal={pid} status={pstatus}", audit_path, proposal_id=pid)
        print(json.dumps({
            "status": "rejected",
            "reason": "proposal_not_approved",
            "proposal_status": pstatus,
            "error": "Only approved proposals can be written to memory store.",
        }, ensure_ascii=False))
        sys.exit(1)

    if pstatus == "rejected":
        audit("store_rejected", f"proposal={pid} status=rejected", audit_path, proposal_id=pid)
        print(json.dumps({"status": "rejected", "reason": "proposal_rejected"}, ensure_ascii=False))
        sys.exit(1)

    # Create memory entry
    memory = {
        "memory_id": f"mem_{uuid4().hex[:12]}",
        "memory_type": target.get("memory_type", "unknown"),
        "content": target.get("proposed_memory_text", ""),
        "source_candidate_id": target.get("candidate_id"),
        "source_proposal_id": pid,
        "confidence": 0.8,
        "created_at": now_iso(),
        "updated_at": None,
        "last_used_at": None,
        "usage_count": 0,
        "decay_policy": "none",
        "status": "active",
        "tags": [],
    }
    append_jsonl(store_path, memory)
    audit("memory_stored", f"memory_id={memory['memory_id']}", audit_path,
          memory_id=memory["memory_id"], proposal_id=pid)

    print(json.dumps({"status": "stored", "memory": memory}, indent=2, ensure_ascii=False))
    return memory


def list_memory(args, store_path):
    memories = load_jsonl(store_path)
    status_filter = args.status
    if status_filter:
        memories = [m for m in memories if m.get("status") == status_filter]

    limit = min(int(args.limit or 20), 100)
    latest = memories[-limit:]
    print(json.dumps({"memories": latest, "total": len(memories), "filtered": len(latest)}, indent=2, ensure_ascii=False))


def archive_memory(args, store_path, archive_path, audit_path):
    mid = args.memory_id
    reason = args.reason or "manual_archive"
    memories = load_jsonl(store_path)
    target = None
    for i, m in enumerate(memories):
        if m.get("memory_id") == mid:
            target = m
            memories[i]["status"] = "archived"
            memories[i]["updated_at"] = now_iso()
            break

    if target is None:
        print(json.dumps({"status": "error", "reason": f"memory '{mid}' not found"}, ensure_ascii=False))
        sys.exit(1)

    write_jsonl(store_path, memories)

    archive_entry = dict(target)
    archive_entry["archived_at"] = now_iso()
    archive_entry["archive_reason"] = reason
    append_jsonl(archive_path, archive_entry)

    audit("memory_archived", f"memory_id={mid} reason={reason}", audit_path, memory_id=mid)
    print(json.dumps({"status": "archived", "memory_id": mid, "reason": reason}, indent=2, ensure_ascii=False))


def supersede_memory(args, store_path, audit_path):
    mid = args.memory_id
    new_mid = args.new_memory_id
    memories = load_jsonl(store_path)
    target = None
    for i, m in enumerate(memories):
        if m.get("memory_id") == mid:
            target = m
            memories[i]["status"] = "superseded"
            memories[i]["superseded_by"] = new_mid
            memories[i]["updated_at"] = now_iso()
            break

    if target is None:
        print(json.dumps({"status": "error", "reason": f"memory '{mid}' not found"}, ensure_ascii=False))
        sys.exit(1)

    write_jsonl(store_path, memories)
    audit("memory_superseded", f"memory_id={mid} superseded_by={new_mid}", audit_path, memory_id=mid)
    print(json.dumps({"status": "superseded", "memory_id": mid, "superseded_by": new_mid}, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="OnePal Memory Store Manager")
    sub = parser.add_subparsers(dest="command")

    p_store = sub.add_parser("store", help="Store approved proposal as memory")
    p_store.add_argument("--proposal-id", required=True)

    p_list = sub.add_parser("list", help="List memory entries")
    p_list.add_argument("--status", default=None, help="Filter by status")
    p_list.add_argument("--limit", default=20, type=int)

    p_archive = sub.add_parser("archive", help="Archive a memory entry")
    p_archive.add_argument("--memory-id", required=True)
    p_archive.add_argument("--reason", default=None)

    p_supersede = sub.add_parser("supersede", help="Supersede a memory entry")
    p_supersede.add_argument("--memory-id", required=True)
    p_supersede.add_argument("--new-memory-id", required=True)

    # Global path overrides
    for p in [p_store, p_list, p_archive, p_supersede]:
        p.add_argument("--store-log", default=None)
        p.add_argument("--proposals-log", default=None)
        p.add_argument("--archive-log", default=None)
        p.add_argument("--audit-log", default=None)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    store_path = Path(vars(args).get("store_log")) if vars(args).get("store_log") else DEFAULT_STORE_LOG
    proposals_path = Path(vars(args).get("proposals_log")) if vars(args).get("proposals_log") else DEFAULT_PROPOSALS_LOG
    archive_path = Path(vars(args).get("archive_log")) if vars(args).get("archive_log") else DEFAULT_ARCHIVE_LOG
    audit_path = Path(vars(args).get("audit_log")) if vars(args).get("audit_log") else DEFAULT_AUDIT_LOG

    if args.command == "store":
        store_memory(args, store_path, proposals_path, audit_path)
    elif args.command == "list":
        list_memory(args, store_path)
    elif args.command == "archive":
        archive_memory(args, store_path, archive_path, audit_path)
    elif args.command == "supersede":
        supersede_memory(args, store_path, audit_path)


if __name__ == "__main__":
    main()
