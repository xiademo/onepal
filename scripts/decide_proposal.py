#!/usr/bin/env python3
"""OnePal Proposal Decision Script - Task 03-A

Represents the explicit human approval entry point.
Creates an approval_decision and updates proposal status.
Does NOT require a separate approval for the approval action itself.

Usage:
    py scripts/decide_proposal.py --proposal <proposal_id> --decision approved|rejected
                                   --actor user [--expires <ISO8601>]
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_APPROVALS = PROJECT_ROOT / "runtime" / "approvals" / "approval_decisions.jsonl"
PROPOSALS_LOG = PROJECT_ROOT / "runtime" / "approvals" / "proposals.jsonl"
AUDIT_LOG = PROJECT_ROOT / "runtime" / "audit" / "state_mutation_audit.jsonl"


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
                records.append(json.loads(line))
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


def main():
    parser = argparse.ArgumentParser(description="OnePal Proposal Decision")
    parser.add_argument("--proposal", required=True, help="Proposal ID")
    parser.add_argument("--decision", default=None, choices=["approved", "rejected"], help="Decision (not required with --create-fixture)")
    parser.add_argument("--actor", default="user", help="Actor making the decision")
    parser.add_argument("--expires", default=None, help="Expiry timestamp (ISO8601)")
    parser.add_argument("--create-fixture", action="store_true", help="Create a test proposal fixture")
    parser.add_argument("--proposals-log", default=None, help="Path to proposals.jsonl (for test isolation)")
    parser.add_argument("--approvals-log", default=None, help="Path to approval_decisions.jsonl (for test isolation)")
    parser.add_argument("--audit-log", default=None, help="Path to state_mutation_audit.jsonl (for test isolation)")
    args = parser.parse_args()

    proposals_path = Path(args.proposals_log) if args.proposals_log else PROPOSALS_LOG
    approvals_path = Path(args.approvals_log) if args.approvals_log else DEFAULT_APPROVALS
    audit_path = Path(args.audit_log) if args.audit_log else AUDIT_LOG

    # === Fixture creation mode ===
    if args.create_fixture:
        prop_id = args.proposal
        proposals = load_jsonl(proposals_path)
        existing = [p for p in proposals if p.get("proposal_id") == prop_id]
        if existing:
            print(json.dumps({"status": "error", "reason": f"proposal '{prop_id}' already exists"}, ensure_ascii=False))
            sys.exit(1)

        proposal = {
            "proposal_id": prop_id,
            "proposal_type": "test_fixture",
            "title": f"Test Proposal {prop_id}",
            "summary": "Auto-created test fixture for Task 03-A validation.",
            "source_agent": "coordinator",
            "risk_level": "R2",
            "status": "pending_review",
            "created_at": now_iso(),
        }
        append_jsonl(proposals_path, proposal)
        print(json.dumps({"status": "created", "proposal": proposal}, indent=2, ensure_ascii=False))
        sys.exit(0)

    # === Validate decision argument ===
    if not args.create_fixture and args.decision is None:
        print(json.dumps({"status": "error", "reason": "--decision is required (approved or rejected)"}, ensure_ascii=False))
        sys.exit(1)

    # === Load existing proposal ===
    proposals = load_jsonl(proposals_path)
    target_idx = None
    target_proposal = None
    for idx, p in enumerate(proposals):
        if p.get("proposal_id") == args.proposal:
            target_idx = idx
            target_proposal = p
            break

    if target_idx is None or target_proposal is None:
        result = {
            "status": "error",
            "reason": f"proposal '{args.proposal}' not found",
            "hint": "Use --create-fixture to create a test proposal first.",
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    # === Validate current proposal state ===
    pstatus = target_proposal.get("status", "")
    if pstatus not in ("draft", "pending_review"):
        result = {
            "status": "error",
            "reason": f"proposal '{args.proposal}' is in non-decidable state '{pstatus}'",
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    # === Create approval decision ===
    approval_id = f"approval_{uuid4().hex[:12]}"
    expires_at = args.expires or (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    approval = {
        "approval_decision_id": approval_id,
        "proposal_id": args.proposal,
        "approval_scope": "single_proposal",
        "approver": args.actor,
        "status": args.decision,
        "created_at": now_iso(),
        "expires_at": expires_at,
        "revocation_allowed": True,
        "one_time_only": True,
    }
    append_jsonl(approvals_path, approval)

    # === Update proposal status ===
    new_status = "approved" if args.decision == "approved" else "rejected"
    proposals[target_idx]["status"] = new_status
    proposals[target_idx]["updated_at"] = now_iso()
    proposals[target_idx]["approval_ref"] = approval_id
    write_jsonl(proposals_path, proposals)

    # === Write audit ===
    audit_entry = {
        "transition_id": f"trans_{uuid4().hex[:12]}",
        "object_id": args.proposal,
        "object_type": "proposal",
        "from_status": pstatus,
        "to_status": new_status,
        "actor": args.actor,
        "reason": f"Proposal decided as {args.decision} (approval: {approval_id})",
        "created_at": now_iso(),
    }
    append_jsonl(audit_path, audit_entry)

    result = {
        "status": "success",
        "proposal_id": args.proposal,
        "decision": args.decision,
        "approval_decision_id": approval_id,
        "proposal_status": new_status,
        "audit_transition_id": audit_entry["transition_id"],
        "expires_at": expires_at,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
