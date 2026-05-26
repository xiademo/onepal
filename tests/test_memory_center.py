#!/usr/bin/env python3
"""OnePal Memory Center Tests - Task 08-B (T1-T17 + regression)

Usage: py tests/test_memory_center.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = "py"
CANDIDATE_SCRIPT = PROJECT_ROOT / "scripts" / "memory_candidate.py"
STORE_SCRIPT = PROJECT_ROOT / "scripts" / "memory_store.py"

passed = 0
failed = 0


def run_cmd(cmd, timeout=60):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                            encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or ""), (result.stderr or "")


def test(name, ok, msg=""):
    global passed, failed
    if ok:
        passed += 1; print(f"  [PASS] {name}")
    else:
        failed += 1; print(f"  [FAIL] {name}")
        if msg:
            for line in str(msg).split("\n")[:3]: print(f"         {line}")
    return ok


def count_jsonl(path):
    if not path.exists(): return 0
    cnt = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try: json.loads(line); cnt += 1
                except json.JSONDecodeError: pass
    return cnt


# T1: memory/README.md exists
def test_T1():
    print("\n--- T1: memory/README.md exists ---")
    return test("T1: memory/README.md exists", (PROJECT_ROOT / "memory" / "README.md").exists())

# T2: create candidate
def test_T2(tmpdir):
    print("\n--- T2: memory candidate created ---")
    cand_log = tmpdir / "candidates.jsonl"
    audit_log = tmpdir / "audit.jsonl"
    ec, out, _ = run_cmd([PY, str(CANDIDATE_SCRIPT), "create",
                           "--content", "Project uses Python 3.11",
                           "--memory-type", "project_decision",
                           "--sensitivity", "internal",
                           "--candidates-log", str(cand_log),
                           "--audit-log", str(audit_log)])
    try: data = json.loads(out.strip())
    except: return test("T2: parse", False, out[:200])
    ok = data.get("status") == "created" and data["candidate"]["candidate_id"].startswith("memcand_")
    return test("T2: candidate created", ok, str(data.get("status")))

# T3: candidate JSONL parseable
def test_T3(tmpdir):
    print("\n--- T3: candidate JSONL parseable ---")
    cand_log = tmpdir / "c.jsonl"
    run_cmd([PY, str(CANDIDATE_SCRIPT), "create", "--content", "Test", "--candidates-log", str(cand_log), "--audit-log", str(tmpdir / "a.jsonl")])
    cnt = count_jsonl(cand_log)
    return test("T3: candidate JSONL parseable", cnt > 0, f"lines={cnt}")

# T4: missing required field rejected
def test_T4(tmpdir):
    print("\n--- T4: missing content rejected ---")
    cand_log = tmpdir / "c.jsonl"
    ec, out, _ = run_cmd([PY, str(CANDIDATE_SCRIPT), "create",
                           "--content", "",
                           "--candidates-log", str(cand_log),
                           "--audit-log", str(tmpdir / "a.jsonl")])
    ok = ec != 0
    return test("T4: empty content rejected", ok, f"exit={ec}")

# T5: forbidden sensitivity rejected
def test_T5(tmpdir):
    print("\n--- T5: forbidden sensitivity rejected ---")
    cand_log = tmpdir / "c.jsonl"
    aud_log = tmpdir / "a.jsonl"
    ec, out, _ = run_cmd([PY, str(CANDIDATE_SCRIPT), "create",
                           "--content", "Some forbidden content",
                           "--sensitivity", "forbidden",
                           "--candidates-log", str(cand_log),
                           "--audit-log", str(aud_log)])
    ok = ec != 0
    return test("T5: forbidden sensitivity rejected", ok, f"exit={ec}")

# T6: secret-like content rejected
def test_T6(tmpdir):
    print("\n--- T6: secret-like content rejected ---")
    cand_log = tmpdir / "c.jsonl"
    ec, out, _ = run_cmd([PY, str(CANDIDATE_SCRIPT), "create",
                           "--content", "sk-abc123def456ghi789jkl012mno345pqr678stu",
                           "--sensitivity", "internal",
                           "--candidates-log", str(cand_log),
                           "--audit-log", str(tmpdir / "a.jsonl")])
    ok = ec != 0
    return test("T6: secret content rejected", ok, f"exit={ec}")

# T7: candidate → proposal
def test_T7(tmpdir):
    print("\n--- T7: candidate → proposal conversion ---")
    cand_log = tmpdir / "c.jsonl"
    prop_log = tmpdir / "p.jsonl"
    aud_log = tmpdir / "a.jsonl"
    run_cmd([PY, str(CANDIDATE_SCRIPT), "create", "--content", "Test proposal", "--memory-type", "system_rule",
             "--candidates-log", str(cand_log), "--audit-log", str(aud_log), "--sensitivity", "internal"])
    cands = []
    with open(cand_log, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line: cands.append(json.loads(line))
    cid = cands[-1]["candidate_id"]

    ec, out, _ = run_cmd([PY, str(CANDIDATE_SCRIPT), "propose", "--candidate-id", cid,
                           "--candidates-log", str(cand_log), "--proposals-log", str(prop_log),
                           "--audit-log", str(aud_log)])
    try: data = json.loads(out.strip())
    except: return test("T7: parse", False, out[:200])
    ok = data.get("status") == "proposed" and data["proposal"]["proposal_id"].startswith("memprop_")
    return test("T7: candidate → proposal", ok, str(data.get("status")))

# T8: unapproved proposal rejected
def test_T8(tmpdir):
    print("\n--- T8: unapproved proposal cannot enter store ---")
    prop_log = tmpdir / "p.jsonl"
    proposal = {"proposal_id": "memprop_unapproved", "proposal_type": "memory_write",
                "proposed_memory_text": "test", "memory_type": "project_decision",
                "status": "pending_review", "created_at": "2026-01-01T00:00:00Z"}
    with open(prop_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(proposal) + "\n")

    ec, out, _ = run_cmd([PY, str(STORE_SCRIPT), "store", "--proposal-id", "memprop_unapproved",
                           "--proposals-log", str(prop_log),
                           "--store-log", str(tmpdir / "s.jsonl"),
                           "--audit-log", str(tmpdir / "a.jsonl")])
    ok = ec != 0
    return test("T8: unapproved proposal rejected", ok, f"exit={ec}")

# T9: approved proposal → store
def test_T9(tmpdir):
    print("\n--- T9: approved proposal written to store ---")
    prop_log = tmpdir / "p.jsonl"
    store_log = tmpdir / "s.jsonl"
    proposal = {"proposal_id": "memprop_approved", "proposal_type": "memory_write",
                "proposed_memory_text": "Approved test memory", "memory_type": "system_rule",
                "status": "approved", "created_at": "2026-01-01T00:00:00Z"}
    with open(prop_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(proposal) + "\n")

    ec, out, _ = run_cmd([PY, str(STORE_SCRIPT), "store", "--proposal-id", "memprop_approved",
                           "--proposals-log", str(prop_log), "--store-log", str(store_log),
                           "--audit-log", str(tmpdir / "a.jsonl")])
    try: data = json.loads(out.strip())
    except: return test("T9: parse", False, out[:200])
    cnt = count_jsonl(store_log)
    ok = data.get("status") == "stored" and cnt > 0
    return test("T9: approved → store", ok, f"status={data.get('status')}, lines={cnt}")

# T10: rejected proposal → not stored
def test_T10(tmpdir):
    print("\n--- T10: rejected proposal not stored ---")
    prop_log = tmpdir / "p10.jsonl"
    store_log = tmpdir / "s10.jsonl"
    proposal = {"proposal_id": "memprop_rejected", "proposal_type": "memory_write",
                "proposed_memory_text": "Rejected", "status": "rejected", "created_at": "2026-01-01T00:00:00Z"}
    with open(prop_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(proposal) + "\n")
    ec, out, _ = run_cmd([PY, str(STORE_SCRIPT), "store", "--proposal-id", "memprop_rejected",
                           "--proposals-log", str(prop_log), "--store-log", str(store_log),
                           "--audit-log", str(tmpdir / "a.jsonl")])
    cnt = count_jsonl(store_log)
    return test("T10: rejected → not stored", cnt == 0 and ec != 0, f"exit={ec}, lines={cnt}")

# T11: duplicate candidate deduped
def test_T11(tmpdir):
    print("\n--- T11: duplicate candidate not duplicated ---")
    cand_log = tmpdir / "c.jsonl"
    prop_log = tmpdir / "p.jsonl"
    aud_log = tmpdir / "a.jsonl"
    # Create first
    run_cmd([PY, str(CANDIDATE_SCRIPT), "create", "--content", "Dedup test content",
             "--memory-type", "workflow_preference", "--sensitivity", "internal",
             "--candidates-log", str(cand_log), "--audit-log", str(aud_log)])
    # Create second (same content = same dedupe key)
    run_cmd([PY, str(CANDIDATE_SCRIPT), "create", "--content", "Dedup test content",
             "--memory-type", "workflow_preference", "--sensitivity", "internal",
             "--candidates-log", str(cand_log), "--audit-log", str(aud_log)])
    cands = []
    with open(cand_log, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line: cands.append(json.loads(line))
    # Propose the second one — should be deduped
    cid = cands[-1]["candidate_id"]
    ec, out, _ = run_cmd([PY, str(CANDIDATE_SCRIPT), "propose", "--candidate-id", cid,
                           "--candidates-log", str(cand_log), "--proposals-log", str(prop_log),
                           "--audit-log", str(aud_log)])
    ok = ec != 0  # Deduped = rejected exit
    return test("T11: duplicate deduped", ok, f"exit={ec}")

# T13: archived memory not in active
def test_T13(tmpdir):
    print("\n--- T13: archived memory not in active list ---")
    store_log = tmpdir / "s.jsonl"
    arch_log = tmpdir / "arch.jsonl"
    aud_log = tmpdir / "a.jsonl"
    memory = {"memory_id": "mem_to_archive", "content": "Will be archived", "status": "active",
              "created_at": "2026-01-01T00:00:00Z"}
    with open(store_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(memory) + "\n")
    run_cmd([PY, str(STORE_SCRIPT), "archive", "--memory-id", "mem_to_archive",
             "--store-log", str(store_log), "--archive-log", str(arch_log),
             "--audit-log", str(aud_log), "--reason", "test"])
    # Read back
    with open(store_log, "r", encoding="utf-8") as f:
        m = json.loads(f.readline())
    ok = m.get("status") == "archived"
    return test("T13: archived → not active", ok, f"status={m.get('status')}")

# T14: superseded retains source
def test_T14(tmpdir):
    print("\n--- T14: superseded retains source reference ---")
    store_log = tmpdir / "s.jsonl"
    aud_log = tmpdir / "a.jsonl"
    mem1 = {"memory_id": "mem_old", "content": "Old", "status": "active", "created_at": "2026-01-01T00:00:00Z"}
    mem2 = {"memory_id": "mem_new", "content": "New", "status": "active", "created_at": "2026-01-02T00:00:00Z"}
    with open(store_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(mem1) + "\n" + json.dumps(mem2) + "\n")
    run_cmd([PY, str(STORE_SCRIPT), "supersede", "--memory-id", "mem_old", "--new-memory-id", "mem_new",
             "--store-log", str(store_log), "--audit-log", str(aud_log)])
    with open(store_log, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    m = next((m for m in lines if m["memory_id"] == "mem_old"), {})
    ok = m.get("status") == "superseded" and m.get("superseded_by") == "mem_new"
    return test("T14: superseded retains reference", ok, f"status={m.get('status')}")

# T15: memory audit log parseable
def test_T15(tmpdir):
    print("\n--- T15: memory audit log parseable ---")
    aud_log = tmpdir / "a.jsonl"
    cand_log = tmpdir / "c.jsonl"
    run_cmd([PY, str(CANDIDATE_SCRIPT), "create", "--content", "Audit test",
             "--candidates-log", str(cand_log), "--audit-log", str(aud_log),
             "--sensitivity", "internal"])
    cnt = count_jsonl(aud_log)
    return test("T15: audit log parseable", cnt > 0, f"lines={cnt}")

# T16: store contains no secrets
def test_T16(tmpdir):
    print("\n--- T16: store contains no secrets ---")
    prop_log = tmpdir / "p.jsonl"
    store_log = tmpdir / "s.jsonl"
    proposal = {"proposal_id": "memprop_clean", "proposal_type": "memory_write",
                "proposed_memory_text": "Clean memory with no secrets", "memory_type": "project_state",
                "status": "approved", "created_at": "2026-01-01T00:00:00Z"}
    with open(prop_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(proposal) + "\n")
    run_cmd([PY, str(STORE_SCRIPT), "store", "--proposal-id", "memprop_clean",
             "--proposals-log", str(prop_log), "--store-log", str(store_log),
             "--audit-log", str(tmpdir / "a.jsonl")])
    with open(store_log, "r", encoding="utf-8") as f:
        content = f.read()
    no_secrets = "sk-" not in content and "token" not in content.lower()
    return test("T16: store has no secrets", no_secrets)

# T17: memory data gitignored
def test_T17():
    print("\n--- T17: memory data gitignored ---")
    ec, stdout, _ = run_cmd(["git", "check-ignore", "-v", "memory/store/memory_store.jsonl"], timeout=10)
    ec2, _, _ = run_cmd(["git", "check-ignore", "-v", "memory/candidates/memory_candidates.jsonl"], timeout=10)
    ec3, _, _ = run_cmd(["git", "check-ignore", "-v", "logs/memory_audit.jsonl"], timeout=10)
    ok = ec == 0 and ec2 == 0 and ec3 == 0
    return test("T17: memory JSONL gitignored", ok, f"store={ec==0} cands={ec2==0} audit={ec3==0}")


def main():
    global passed, failed
    print("=" * 60)
    print("OnePal Memory Center Tests (T1-T17)")
    print("=" * 60)

    test_T1()

    with tempfile.TemporaryDirectory(prefix="onepal_mem_test_") as td:
        tmpdir = Path(td)
        test_T2(tmpdir); test_T3(tmpdir); test_T4(tmpdir); test_T5(tmpdir)
        test_T6(tmpdir); test_T7(tmpdir); test_T8(tmpdir); test_T9(tmpdir)
        test_T10(tmpdir); test_T11(tmpdir); test_T13(tmpdir); test_T14(tmpdir)
        test_T15(tmpdir); test_T16(tmpdir)

    test_T17()

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
