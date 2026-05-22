#!/usr/bin/env python3
"""OnePal Governance Loop Tests - Task 03-B

Automated test suite for the action/permission/approval closed loop.
Uses Python standard library only. No pytest required.

Usage:
    py tests/test_governance_loop.py

T1-T12: Full governance guard coverage
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
REGISTRY = PROJECT_ROOT / "registries" / "action_registry.json"
PROFILES = PROJECT_ROOT / "policies" / "permission_profiles.json"

# Test-specific runtime paths (isolated from real runtime)
TEST_RUNTIME = Path(os.environ.get("TEMP", "/tmp")) / "onepal_test_runtime"
TEST_EXECUTIONS = TEST_RUNTIME / "actions" / "action_executions.jsonl"
TEST_AUDIT = TEST_RUNTIME / "audit" / "state_mutation_audit.jsonl"
TEST_PROPOSALS = TEST_RUNTIME / "approvals" / "proposals.jsonl"
TEST_APPROVALS = TEST_RUNTIME / "approvals" / "approval_decisions.jsonl"
TEST_REGISTRY = TEST_RUNTIME / "test_action_registry.json"
TEST_PROFILES = TEST_RUNTIME / "test_permission_profiles.json"

PY = "py"
passed = 0
failed = 0


def setup():
    """Create isolated test runtime directories and copy fixtures."""
    for d in [TEST_RUNTIME / "actions", TEST_RUNTIME / "audit", TEST_RUNTIME / "approvals"]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy registries for test isolation
    shutil.copy2(REGISTRY, TEST_REGISTRY)
    shutil.copy2(PROFILES, TEST_PROFILES)

    # Clean any existing test JSONL
    for f in [TEST_EXECUTIONS, TEST_AUDIT, TEST_PROPOSALS, TEST_APPROVALS]:
        if f.exists():
            f.unlink()


def teardown():
    """Clean up test runtime data."""
    shutil.rmtree(TEST_RUNTIME, ignore_errors=True)


def run(cmd, expect_exit=0, expect_contains=None):
    """Run a command, check exit code and optional output substring."""
    full_cmd = [PY, "-u"] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
    ok = True
    msg = result.stdout.strip() + result.stderr.strip()

    if result.returncode != expect_exit:
        ok = False
        msg = f"expected exit {expect_exit}, got {result.returncode}\n{msg}"

    if expect_contains and ok:
        if expect_contains not in result.stdout + result.stderr:
            ok = False
            msg = f"expected output containing '{expect_contains}'\n{msg}"

    return ok, msg


def test(name, ok, msg=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")
        if msg:
            for line in msg.split("\n"):
                print(f"         {line}")
    return ok


def count_jsonl_lines(path):
    """Count valid JSONL lines in a file."""
    if not path.exists():
        return 0
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    json.loads(line)
                    count += 1
                except json.JSONDecodeError:
                    pass
    return count


# ============================================================================
# T1: Unregistered action rejected
# ============================================================================
def test_T1():
    print("\n--- T1: Unregistered action rejected ---")
    ok, msg = run([
        str(SCRIPTS / "request_action.py"),
        "--action", "action.not_exist",
        "--profile", "safe_readonly",
        "--executions-log", str(TEST_EXECUTIONS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=1, expect_contains="not registered")
    return test("T1: unregistered action rejected", ok, msg)


# ============================================================================
# T2: safe_readonly dry-run read_file
# ============================================================================
def test_T2():
    print("\n--- T2: safe_readonly dry-run read_file ---")
    ok, msg = run([
        str(SCRIPTS / "request_action.py"),
        "--action", "action.read_file",
        "--profile", "safe_readonly",
        "--dry-run",
        "--executions-log", str(TEST_EXECUTIONS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=0)
    return test("T2: safe_readonly dry-run", ok, msg)


# ============================================================================
# T3: R0 read_file no approval needed
# ============================================================================
def test_T3():
    print("\n--- T3: R0 read_file without approval ---")
    ok, msg = run([
        str(SCRIPTS / "request_action.py"),
        "--action", "action.read_file",
        "--profile", "safe_readonly",
        "--executions-log", str(TEST_EXECUTIONS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=0)
    return test("T3: R0 action without approval", ok, msg)


# ============================================================================
# T4: R2 approve_proposal without approval rejected
# ============================================================================
def test_T4():
    print("\n--- T4: R2 action without approval rejected ---")
    ok, msg = run([
        str(SCRIPTS / "request_action.py"),
        "--action", "action.approve_proposal",
        "--profile", "local_write_with_approval",
        "--executions-log", str(TEST_EXECUTIONS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=1, expect_contains="approval required")
    return test("T4: R2 action without approval rejected", ok, msg)


# ============================================================================
# T5: safe_readonly cannot approve
# ============================================================================
def test_T5():
    print("\n--- T5: safe_readonly cannot approve ---")
    ok, msg = run([
        str(SCRIPTS / "request_action.py"),
        "--action", "action.approve_proposal",
        "--profile", "safe_readonly",
        "--executions-log", str(TEST_EXECUTIONS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=1, expect_contains="deny")
    return test("T5: safe_readonly cannot approve", ok, msg)


# ============================================================================
# T6: create_proposal dry-run
# ============================================================================
def test_T6():
    print("\n--- T6: create_proposal dry-run ---")
    ok, msg = run([
        str(SCRIPTS / "request_action.py"),
        "--action", "action.create_proposal",
        "--profile", "safe_readonly",
        "--dry-run",
        "--executions-log", str(TEST_EXECUTIONS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=0)
    return test("T6: create_proposal dry-run", ok, msg)


# ============================================================================
# T7: rejected proposal cannot execute
# ============================================================================
def test_T7():
    print("\n--- T7: rejected proposal blocked ---")
    # Create proposal fixture
    run([
        str(SCRIPTS / "decide_proposal.py"),
        "--proposal", "prop_t7_test",
        "--create-fixture",
        "--proposals-log", str(TEST_PROPOSALS),
        "--approvals-log", str(TEST_APPROVALS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=0)

    # Reject it
    run([
        str(SCRIPTS / "decide_proposal.py"),
        "--proposal", "prop_t7_test",
        "--decision", "rejected",
        "--actor", "test",
        "--proposals-log", str(TEST_PROPOSALS),
        "--approvals-log", str(TEST_APPROVALS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=0)

    # Try to execute with rejected proposal
    ok, msg = run([
        str(SCRIPTS / "request_action.py"),
        "--action", "action.approve_proposal",
        "--profile", "local_write_with_approval",
        "--proposal", "prop_t7_test",
        "--proposals-log", str(TEST_PROPOSALS),
        "--approvals-log", str(TEST_APPROVALS),
        "--executions-log", str(TEST_EXECUTIONS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=1)
    return test("T7: rejected proposal blocked", ok, msg)


# ============================================================================
# T8: state_mutation writes audit
# ============================================================================
def test_T8():
    print("\n--- T8: state_mutation writes audit ---")
    # Create and approve a proposal
    run([
        str(SCRIPTS / "decide_proposal.py"),
        "--proposal", "prop_t8_test",
        "--create-fixture",
        "--proposals-log", str(TEST_PROPOSALS),
        "--approvals-log", str(TEST_APPROVALS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=0)

    run([
        str(SCRIPTS / "decide_proposal.py"),
        "--proposal", "prop_t8_test",
        "--decision", "approved",
        "--actor", "test",
        "--proposals-log", str(TEST_PROPOSALS),
        "--approvals-log", str(TEST_APPROVALS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=0)

    # Get the approval ID
    approvals = []
    if TEST_APPROVALS.exists():
        with open(TEST_APPROVALS, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    approvals.append(json.loads(line))
    approval_id = approvals[-1]["approval_decision_id"] if approvals else None

    if not approval_id:
        return test("T8: state_mutation audit", False, "could not get approval ID")

    # Count audit lines before
    audit_before = count_jsonl_lines(TEST_AUDIT)

    # Execute state_mutation action with valid approval
    run([
        str(SCRIPTS / "request_action.py"),
        "--action", "action.approve_proposal",
        "--profile", "local_write_with_approval",
        "--approval", approval_id,
        "--proposal", "prop_t8_test",
        "--proposals-log", str(TEST_PROPOSALS),
        "--approvals-log", str(TEST_APPROVALS),
        "--executions-log", str(TEST_EXECUTIONS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=0)

    # Count audit lines after
    audit_after = count_jsonl_lines(TEST_AUDIT)
    ok = audit_after > audit_before
    return test("T8: state_mutation writes audit", ok, f"before={audit_before}, after={audit_after}")


# ============================================================================
# T9: action_executions.jsonl has records
# ============================================================================
def test_T9():
    print("\n--- T9: action_executions.jsonl has records ---")
    count = count_jsonl_lines(TEST_EXECUTIONS)
    ok = count > 0
    return test("T9: execution records exist", ok, f"count={count}")


# ============================================================================
# T10: all runtime JSONL lines parseable
# ============================================================================
def test_T10():
    print("\n--- T10: all runtime JSONL parseable ---")
    all_ok = True
    bad = 0
    for log_path in [TEST_EXECUTIONS, TEST_AUDIT, TEST_PROPOSALS, TEST_APPROVALS]:
        if not log_path.exists():
            continue
        with open(log_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    bad += 1
                    all_ok = False
    return test("T10: JSONL parseable", all_ok, f"bad_lines={bad}")


# ============================================================================
# T11: disabled action rejected (G2)
# ============================================================================
def test_T11():
    print("\n--- T11: disabled action rejected (G2) ---")
    # Create a modified registry with action.read_file disabled
    with open(REGISTRY, "r", encoding="utf-8") as f:
        reg_data = json.load(f)

    modified = json.loads(json.dumps(reg_data))  # deep copy
    for action in modified["actions"]:
        if action["action_id"] == "action.read_file":
            action["enabled"] = False
            break

    disabled_registry = TEST_RUNTIME / "disabled_action_registry.json"
    with open(disabled_registry, "w", encoding="utf-8") as f:
        json.dump(modified, f, indent=2, ensure_ascii=False)

    ok, msg = run([
        str(SCRIPTS / "request_action.py"),
        "--action", "action.read_file",
        "--profile", "safe_readonly",
        "--registry", str(disabled_registry),
        "--profiles", str(TEST_PROFILES),
        "--executions-log", str(TEST_EXECUTIONS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=1, expect_contains="disabled")

    return test("T11: disabled action rejected (G2)", ok, msg)


# ============================================================================
# T12: expired approval rejected (G5)
# ============================================================================
def test_T12():
    print("\n--- T12: expired approval rejected (G5) ---")
    # Create a proposal
    run([
        str(SCRIPTS / "decide_proposal.py"),
        "--proposal", "prop_t12_test",
        "--create-fixture",
        "--proposals-log", str(TEST_PROPOSALS),
        "--approvals-log", str(TEST_APPROVALS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=0)

    # Approve with past expiry
    past_expiry = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    run([
        str(SCRIPTS / "decide_proposal.py"),
        "--proposal", "prop_t12_test",
        "--decision", "approved",
        "--actor", "test",
        "--expires", past_expiry,
        "--proposals-log", str(TEST_PROPOSALS),
        "--approvals-log", str(TEST_APPROVALS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=0)

    # Get the expired approval ID
    approvals = []
    if TEST_APPROVALS.exists():
        with open(TEST_APPROVALS, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    approvals.append(json.loads(line))
    expired_id = None
    for a in reversed(approvals):
        if a.get("proposal_id") == "prop_t12_test":
            expired_id = a["approval_decision_id"]
            break

    if not expired_id:
        return test("T12: expired approval rejected", False, "no expired approval found")

    ok, msg = run([
        str(SCRIPTS / "request_action.py"),
        "--action", "action.approve_proposal",
        "--profile", "local_write_with_approval",
        "--approval", expired_id,
        "--proposal", "prop_t12_test",
        "--proposals-log", str(TEST_PROPOSALS),
        "--approvals-log", str(TEST_APPROVALS),
        "--executions-log", str(TEST_EXECUTIONS),
        "--audit-log", str(TEST_AUDIT),
    ], expect_exit=1, expect_contains="expired")

    return test("T12: expired approval rejected (G5)", ok, msg)


# ============================================================================
# Main
# ============================================================================
def main():
    global passed, failed

    print("=" * 60)
    print("OnePal Governance Loop Tests")
    print("=" * 60)

    setup()

    test_T1()
    test_T2()
    test_T3()
    test_T4()
    test_T5()
    test_T6()
    test_T7()
    test_T8()
    test_T9()
    test_T10()
    test_T11()
    test_T12()

    teardown()

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
