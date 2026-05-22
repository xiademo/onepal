#!/usr/bin/env python3
"""OnePal Action Request Script - Task 03-A

Accepts an action request, applies 7 guard checks, and records execution.

Guards:
  G1: Action must be registered in action_registry.json
  G2: Action must be enabled
  G3: Profile must authorize the action (via permission_profiles.json)
  G4: R2+ or approval_required actions need an active approval decision
  G5: Approval decision must not be expired
  G6: Proposals in rejected/expired state cannot trigger execution
  G7: state_mutation=true actions must write an audit entry

Usage:
    py scripts/request_action.py --action <action_id> --profile <profile_id>
                                 [--approval <approval_id>] [--proposal <proposal_id>]
                                 [--dry-run]
"""

import argparse
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ACTION_REGISTRY = PROJECT_ROOT / "registries" / "action_registry.json"
PERMISSION_PROFILES = PROJECT_ROOT / "policies" / "permission_profiles.json"
DEFAULT_EXECUTIONS_LOG = PROJECT_ROOT / "runtime" / "actions" / "action_executions.jsonl"
DEFAULT_AUDIT_LOG = PROJECT_ROOT / "runtime" / "audit" / "state_mutation_audit.jsonl"
PROPOSALS_LOG = PROJECT_ROOT / "runtime" / "approvals" / "proposals.jsonl"
APPROVALS_LOG = PROJECT_ROOT / "runtime" / "approvals" / "approval_decisions.jsonl"

FORBIDDEN_PATTERNS = [".env", "secrets", "credentials", "token", "OpenCode"]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    """Load all records from a JSONL file."""
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def append_jsonl(path, record):
    """Append a single JSON record to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure no trailing newline issues
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def find_action(registry, action_id):
    for a in registry.get("actions", []):
        if a["action_id"] == action_id:
            return a
    return None


def find_profile(profiles_data, profile_id):
    for p in profiles_data.get("profiles", []):
        if p["profile_id"] == profile_id:
            return p
    return None


def find_approval(approval_id, log_path=None):
    path = log_path or APPROVALS_LOG
    records = load_jsonl(path)
    for r in records:
        if r.get("approval_decision_id") == approval_id:
            return r
    return None


def find_proposal(proposal_id, log_path=None):
    path = log_path or PROPOSALS_LOG
    records = load_jsonl(path)
    for r in records:
        if r.get("proposal_id") == proposal_id:
            return r
    return None


def is_expired(approval):
    try:
        expires = approval.get("expires_at", "")
        if expires:
            exp_dt = datetime.fromisoformat(expires)
            return datetime.now(timezone.utc) > exp_dt
    except (ValueError, TypeError):
        return True  # unparseable expiry = treated as expired
    return False


def main():
    parser = argparse.ArgumentParser(description="OnePal Action Request")
    parser.add_argument("--action", required=True, help="Action ID")
    parser.add_argument("--profile", required=True, help="Profile ID")
    parser.add_argument("--approval", default=None, help="Approval Decision ID")
    parser.add_argument("--proposal", default=None, help="Proposal ID")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--path", default=None, help="File path for read actions")
    parser.add_argument("--registry", default=None, help="Path to action_registry.json (default: registries/action_registry.json)")
    parser.add_argument("--profiles", default=None, help="Path to permission_profiles.json (default: policies/permission_profiles.json)")
    parser.add_argument("--executions-log", default=None, help="Path to action_executions.jsonl (for testing)")
    parser.add_argument("--audit-log", default=None, help="Path to state_mutation_audit.jsonl (for testing)")
    parser.add_argument("--proposals-log", default=None, help="Path to proposals.jsonl (for test isolation)")
    parser.add_argument("--approvals-log", default=None, help="Path to approval_decisions.jsonl (for test isolation)")
    args = parser.parse_args()

    registry_path = Path(args.registry) if args.registry else ACTION_REGISTRY
    profiles_path = Path(args.profiles) if args.profiles else PERMISSION_PROFILES
    exec_log = Path(args.executions_log) if args.executions_log else DEFAULT_EXECUTIONS_LOG
    audit_log = Path(args.audit_log) if args.audit_log else DEFAULT_AUDIT_LOG
    proposals_log = Path(args.proposals_log) if args.proposals_log else PROPOSALS_LOG
    approvals_log = Path(args.approvals_log) if args.approvals_log else APPROVALS_LOG

    execution_id = f"actexec_{uuid4().hex[:12]}"
    result = {
        "execution_id": execution_id,
        "action_id": args.action,
        "profile_id": args.profile,
        "started_at": now_iso(),
        "guard_results": [],
    }

    # Load registries
    registry = load_json(registry_path)
    profiles_data = load_json(profiles_path)
    action = find_action(registry, args.action)
    profile = find_profile(profiles_data, args.profile)

    # === G1: Action registered ===
    if action is None:
        result["status"] = "failed"
        result["reason"] = f"G1: action '{args.action}' not registered"
        result["guard_results"].append({"guard": "G1", "passed": False, "reason": "action_not_registered"})
        append_jsonl(exec_log, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)
    result["guard_results"].append({"guard": "G1", "passed": True})

    # === G2: Action enabled ===
    if not action.get("enabled", False):
        result["status"] = "failed"
        result["reason"] = "G2: action is disabled"
        result["guard_results"].append({"guard": "G2", "passed": False, "reason": "action_disabled"})
        append_jsonl(exec_log, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)
    result["guard_results"].append({"guard": "G2", "passed": True})

    # === G3: Profile authorized ===
    if profile is None:
        result["status"] = "failed"
        result["reason"] = f"G3: profile '{args.profile}' not found"
        result["guard_results"].append({"guard": "G3", "passed": False, "reason": "profile_not_found"})
        append_jsonl(exec_log, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    permissions = profile.get("permissions", {})
    perm = permissions.get(args.action, "deny")

    if perm == "deny":
        result["status"] = "failed"
        result["reason"] = f"G3: action '{args.action}' denied by profile '{args.profile}'"
        result["guard_results"].append({"guard": "G3", "passed": False, "reason": f"permission={perm}"})
        append_jsonl(exec_log, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)
    result["guard_results"].append({"guard": "G3", "passed": True, "permission": perm})

    # === G4: R2+ or approval_required needs approval ===
    risk = action.get("risk_level", "R0")
    needs_approval = action.get("approval_required", False)
    is_high_risk = risk in ("R2", "R3", "R4")

    if is_high_risk or needs_approval:
        if args.approval is None:
            result["status"] = "failed"
            result["reason"] = f"G4: approval required (risk={risk}, approval_required={needs_approval})"
            result["guard_results"].append({"guard": "G4", "passed": False, "reason": "no_approval_provided"})
            append_jsonl(exec_log, result)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

        approval = find_approval(args.approval, approvals_log)
        if approval is None:
            result["status"] = "failed"
            result["reason"] = f"G4: approval '{args.approval}' not found in ledger"
            result["guard_results"].append({"guard": "G4", "passed": False, "reason": "approval_not_found"})
            append_jsonl(exec_log, result)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

        if approval.get("status") != "approved":
            result["status"] = "failed"
            result["reason"] = f"G4: approval '{args.approval}' status is '{approval.get('status')}' (not 'approved')"
            result["guard_results"].append({"guard": "G4", "passed": False, "reason": "approval_not_approved"})
            append_jsonl(exec_log, result)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

        # === G5: Approval not expired ===
        if is_expired(approval):
            result["status"] = "failed"
            result["reason"] = f"G5: approval '{args.approval}' has expired"
            result["guard_results"].append({"guard": "G5", "passed": False, "reason": "approval_expired"})
            append_jsonl(exec_log, result)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)
        result["guard_results"].append({"guard": "G5", "passed": True})
    else:
        result["guard_results"].append({"guard": "G4", "passed": True, "note": "not_required"})
        result["guard_results"].append({"guard": "G5", "passed": True, "note": "not_required"})

    # === G6: Proposal state check ===
    if args.proposal:
        proposal = find_proposal(args.proposal, proposals_log)
        if proposal is None:
            result["status"] = "failed"
            result["reason"] = f"G6: proposal '{args.proposal}' not found"
            result["guard_results"].append({"guard": "G6", "passed": False, "reason": "proposal_not_found"})
            append_jsonl(exec_log, result)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

        pstatus = proposal.get("status", "")
        if pstatus in ("rejected", "auto_rejected", "expired", "cancelled"):
            result["status"] = "failed"
            result["reason"] = f"G6: proposal '{args.proposal}' is in terminal state '{pstatus}'"
            result["guard_results"].append({"guard": "G6", "passed": False, "reason": f"proposal_status={pstatus}"})
            append_jsonl(exec_log, result)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)
        result["guard_results"].append({"guard": "G6", "passed": True, "proposal_status": pstatus})
    else:
        result["guard_results"].append({"guard": "G6", "passed": True, "note": "no_proposal_linked"})

    # === All guards passed - execute action ===
    if args.dry_run:
        result["status"] = "dry_run"
        result["reason"] = "All guards passed (dry run, no state mutation performed)"
        append_jsonl(exec_log, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    # Simulated execution (no real file ops for read_file)
    state_mut = action.get("state_mutation", False)
    if state_mut:
        # === G7: Write audit for state mutation ===
        audit_entry = {
            "transition_id": f"trans_{uuid4().hex[:12]}",
            "object_id": args.proposal or execution_id,
            "object_type": "action_execution",
            "from_status": "guards_passed",
            "to_status": "executing",
            "actor": args.profile,
            "reason": f"Action {args.action} executed",
            "created_at": now_iso(),
        }
        append_jsonl(audit_log, audit_entry)
        result["guard_results"].append({"guard": "G7", "passed": True, "audit_transition_id": audit_entry["transition_id"]})
    else:
        result["guard_results"].append({"guard": "G7", "passed": True, "note": "not_state_mutation"})

    result["status"] = "completed"
    result["ended_at"] = now_iso()
    result["reason"] = f"Action '{args.action}' executed successfully"
    append_jsonl(exec_log, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
