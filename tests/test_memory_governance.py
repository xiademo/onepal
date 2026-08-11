#!/usr/bin/env python3
"""OnePal Memory Governance Tests - Task 14-B.

Usage: py tests/test_memory_governance.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
SCRIPT = PROJECT_ROOT / "scripts" / "memory_governance.py"

passed = 0
failed = 0


def test(name, ok, msg=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")
        if msg:
            for line in str(msg).split("\n")[:3]:
                print(f"         {line}")
    return ok


def run_cmd(cmd, timeout=60):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace")


def append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def base_paths(tmpdir):
    return {
        "candidates": tmpdir / "memory" / "candidates.jsonl",
        "store": tmpdir / "memory" / "store.jsonl",
        "reviews": tmpdir / "memory" / "reviews.jsonl",
        "conflicts": tmpdir / "memory" / "conflicts.jsonl",
        "changes": tmpdir / "memory" / "changes.jsonl",
        "snapshots": tmpdir / "memory" / "snapshots.jsonl",
        "snapshot_dir": tmpdir / "memory" / "snapshot_files",
        "audit": tmpdir / "logs" / "memory_audit.jsonl",
    }


def path_args(paths):
    return [
        "--candidates-log", str(paths["candidates"]),
        "--store-log", str(paths["store"]),
        "--reviews-log", str(paths["reviews"]),
        "--conflicts-log", str(paths["conflicts"]),
        "--changes-log", str(paths["changes"]),
        "--snapshots-log", str(paths["snapshots"]),
        "--snapshot-dir", str(paths["snapshot_dir"]),
        "--audit-log", str(paths["audit"]),
    ]


def seed_candidate(paths, content="Project prefers small verifiable changes."):
    candidate = {
        "candidate_id": "memcand_seed",
        "memory_type": "workflow_preference",
        "content": content,
        "content_summary": content[:200],
        "source_type": "manual",
        "source_agent": "user",
        "confidence": 0.9,
        "sensitivity": "internal",
        "status": "captured",
        "created_at": "2026-06-08T00:00:00Z",
    }
    append_jsonl(paths["candidates"], candidate)
    return candidate


def seed_memory(paths, content="Project prefers small verifiable changes."):
    memory = {
        "memory_id": "mem_existing",
        "memory_type": "workflow_preference",
        "content": content,
        "status": "active",
        "created_at": "2026-06-08T00:00:00Z",
    }
    append_jsonl(paths["store"], memory)
    return memory


def parse_stdout(result):
    try:
        return json.loads((result.stdout or "").strip())
    except json.JSONDecodeError:
        return {"parse_error": result.stdout[:300]}


def test_T1(tmpdir):
    print("\n--- T1: script exists ---")
    return test("T1: memory_governance.py exists", SCRIPT.exists())


def test_T2(tmpdir):
    print("\n--- T2: quality review created ---")
    paths = base_paths(tmpdir / "t2")
    seed_candidate(paths)
    result = run_cmd([PY, str(SCRIPT), "review-create", "--target-type", "candidate",
                      "--target-ref", "memcand_seed"] + path_args(paths))
    data = parse_stdout(result)
    review = data.get("review", {})
    rows = load_jsonl(paths["reviews"])
    ok = result.returncode == 0 and data.get("status") == "created" and review.get("memory_quality_review_id", "").startswith("memqr_") and len(rows) == 1
    return test("T2: quality review created", ok, str(data))


def test_T3(tmpdir):
    print("\n--- T3: secret-like candidate needs rejection review ---")
    paths = base_paths(tmpdir / "t3")
    seed_candidate(paths, "token=abcdef1234567890 should never be stored")
    result = run_cmd([PY, str(SCRIPT), "review-create", "--target-type", "candidate",
                      "--target-ref", "memcand_seed"] + path_args(paths))
    data = parse_stdout(result)
    review = data.get("review", {})
    ok = review.get("recommendation") == "reject_candidate" and review.get("requires_user_confirmation") is True
    return test("T3: secret-like candidate rejected by review", ok, str(review))


def test_T4(tmpdir):
    print("\n--- T4: duplicate conflict detected ---")
    paths = base_paths(tmpdir / "t4")
    seed_candidate(paths)
    seed_memory(paths)
    result = run_cmd([PY, str(SCRIPT), "conflict-detect", "--target-type", "candidate",
                      "--target-ref", "memcand_seed"] + path_args(paths))
    data = parse_stdout(result)
    conflict = data.get("conflict", {})
    ok = data.get("status") == "created" and conflict.get("memory_conflict_id", "").startswith("memconf_") and conflict.get("existing_memory_refs") == ["mem_existing"]
    return test("T4: duplicate conflict detected", ok, str(data))


def test_T5(tmpdir):
    print("\n--- T5: no conflict path does not create record ---")
    paths = base_paths(tmpdir / "t5")
    seed_candidate(paths, "This is a distinct preference.")
    seed_memory(paths, "Completely different memory.")
    result = run_cmd([PY, str(SCRIPT), "conflict-detect", "--target-type", "candidate",
                      "--target-ref", "memcand_seed"] + path_args(paths))
    data = parse_stdout(result)
    ok = data.get("status") == "no_conflict" and load_jsonl(paths["conflicts"]) == []
    return test("T5: no conflict stays empty", ok, str(data))


def test_T6(tmpdir):
    print("\n--- T6: change request created without direct store write ---")
    paths = base_paths(tmpdir / "t6")
    seed_candidate(paths)
    before = load_jsonl(paths["store"])
    result = run_cmd([PY, str(SCRIPT), "change-create", "--change-type", "create",
                      "--target-refs", "memcand_seed", "--source-candidate-id", "memcand_seed",
                      "--reason", "Create reviewed memory"] + path_args(paths))
    data = parse_stdout(result)
    change = data.get("change_request", {})
    after = load_jsonl(paths["store"])
    ok = (
        data.get("status") == "created"
        and change.get("memory_change_request_id", "").startswith("memchg_")
        and change.get("requires_user_approval") is True
        and change.get("status") == "pending_review"
        and before == after
    )
    return test("T6: change request created without store write", ok, str(data))


def test_T7(tmpdir):
    print("\n--- T7: snapshot created ---")
    paths = base_paths(tmpdir / "t7")
    seed_memory(paths)
    result = run_cmd([PY, str(SCRIPT), "snapshot-create", "--reason", "Before memory change"] + path_args(paths))
    data = parse_stdout(result)
    snap = data.get("snapshot", {})
    payload_path = Path(snap.get("storage_path", ""))
    ok = (
        data.get("status") == "created"
        and snap.get("memory_snapshot_id", "").startswith("memsnap_")
        and len(snap.get("content_hash", "")) == 64
        and snap.get("entry_count") == 1
        and payload_path.exists()
    )
    return test("T7: snapshot metadata and payload created", ok, str(snap))


def test_T8(tmpdir):
    print("\n--- T8: list records ---")
    paths = base_paths(tmpdir / "t8")
    seed_candidate(paths)
    run_cmd([PY, str(SCRIPT), "review-create", "--target-type", "candidate",
             "--target-ref", "memcand_seed"] + path_args(paths))
    result = run_cmd([PY, str(SCRIPT), "list", "--record-type", "reviews"] + path_args(paths))
    data = parse_stdout(result)
    ok = data.get("total") == 1 and len(data.get("reviews", [])) == 1
    return test("T8: list reviews returns one record", ok, str(data))


def test_T9():
    print("\n--- T9: static safety ---")
    text = SCRIPT.read_text(encoding="utf-8")
    stripped = "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))
    ok = "shell=True" not in stripped and "http://" not in stripped and "https://" not in stripped
    return test("T9: no shell=True or network URLs", ok)


def main():
    print("=" * 60)
    print("OnePal Memory Governance Tests")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="onepal_memgov_test_") as td:
        tmpdir = Path(td)
        test_T1(tmpdir)
        test_T2(tmpdir)
        test_T3(tmpdir)
        test_T4(tmpdir)
        test_T5(tmpdir)
        test_T6(tmpdir)
        test_T7(tmpdir)
        test_T8(tmpdir)
    test_T9()

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
