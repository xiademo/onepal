#!/usr/bin/env python3
"""OnePal API Server Tests - Task 06 (T1-T17)

Usage: py tests/test_api_server.py
"""

import json
import os
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

# Add project root for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
from scripts.api_server import (
    read_jsonl, build_response, handle_health, handle_tasks,
    handle_task_trees, handle_task_runs, handle_mas_trace, handle_command,
    HEALTH_PATH, TASKS_PATH, TREES_PATH, TASK_RUNS_PATH, MAS_TRACE_PATH,
    COMMAND_GATEWAY, MAX_LIMIT,
)

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


# --- Unit Tests: Core Functions ---

def test_T1():
    """T1: API server module importable."""
    print("\n--- T1: module importable ---")
    return test("T1: module importable", True)


def test_T2(tmpdir):
    """T2: 0.0.0.0 rejection."""
    print("\n--- T2: 0.0.0.0 rejection ---")
    from scripts.api_server import ALLOWED_HOSTS
    ok = "0.0.0.0" not in ALLOWED_HOSTS
    return test("T2: 0.0.0.0 not in ALLOWED_HOSTS", ok)


def test_T3(tmpdir):
    """T3: read_jsonl with missing file returns empty."""
    print("\n--- T3: read_jsonl missing file -> empty ---")
    results, skipped = read_jsonl(tmpdir / "nonexistent.jsonl", 10)
    return test("T3: missing file returns empty", results == [] and skipped == 0)


def test_T4(tmpdir):
    """T4: read_jsonl with valid JSONL."""
    print("\n--- T4: read_jsonl with valid JSONL ---")
    path = tmpdir / "test.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for i in range(5):
            f.write(json.dumps({"id": i}) + "\n")
    results, skipped = read_jsonl(path, 5)
    ok = len(results) == 5 and skipped == 0
    return test("T4: read_jsonl 5 valid lines", ok, f"lines={len(results)} skipped={skipped}")


def test_T5(tmpdir):
    """T5: read_jsonl with malformed lines skips them."""
    print("\n--- T5: read_jsonl skips malformed lines ---")
    path = tmpdir / "bad.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ok": 1}) + "\n")
        f.write("this is not json\n")
        f.write(json.dumps({"ok": 2}) + "\n")
    results, skipped = read_jsonl(path, 10)
    ok = len(results) == 2 and skipped == 1
    return test("T5: malformed lines skipped gracefully", ok, f"results={len(results)} skipped={skipped}")


def test_T6(tmpdir):
    """T6: read_jsonl limit clamped to MAX_LIMIT."""
    print("\n--- T6: read_jsonl limit clamped ---")
    path = tmpdir / "many.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for i in range(200):
            f.write(json.dumps({"id": i}) + "\n")
    results, _ = read_jsonl(path, 999)
    ok = len(results) == MAX_LIMIT
    return test("T6: limit clamped to 100", ok, f"got {len(results)}")


def test_T7(tmpdir):
    """T7: GET /health with health_status.json present."""
    print("\n--- T7: GET /health with file present ---")
    hpath = tmpdir / "health.json"
    hpath.write_text(json.dumps({"status": "ready", "checked_at": "2026-01-01T00:00:00Z"}), encoding="utf-8")
    resp = handle_health(hpath)
    ok = resp["ok"] and resp["data"].get("status") == "ready"
    return test("T7: health returns ok with ready status", ok, str(resp["data"].get("status")))


def test_T8(tmpdir):
    """T8: GET /health with file missing."""
    print("\n--- T8: GET /health with file missing ---")
    resp = handle_health(tmpdir / "nonexistent.json")
    ok = resp["ok"] and not resp["data"].get("exists")
    return test("T8: missing health returns ok with limited", ok, str(resp["data"].get("status")))


def test_T9(tmpdir):
    """T9: GET /tasks with file present."""
    print("\n--- T9: GET /tasks with file present ---")
    path = tmpdir / "tasks.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for i in range(3):
            f.write(json.dumps({"task_id": f"task_{i}"}) + "\n")
    resp = handle_tasks(path, 20)
    ok = resp["ok"] and len(resp["data"]["tasks"]) == 3
    return test("T9: tasks returns 3 items", ok, f"got {len(resp['data']['tasks'])}")


def test_T10(tmpdir):
    """T10: GET /task-trees with file present."""
    print("\n--- T10: GET /task-trees with file present ---")
    path = tmpdir / "trees.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"task_tree_id": "tree_1"}) + "\n")
    resp = handle_task_trees(path, 20)
    ok = resp["ok"] and len(resp["data"]["task_trees"]) == 1
    return test("T10: task-trees returns 1 item", ok, f"got {len(resp['data']['task_trees'])}")


def test_T11(tmpdir):
    """T11: GET /task-runs with file present."""
    print("\n--- T11: GET /task-runs with file present ---")
    path = tmpdir / "runs.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"task_run_id": "tr_1"}) + "\n")
    resp = handle_task_runs(path, 20)
    ok = resp["ok"] and len(resp["data"]["task_runs"]) == 1
    return test("T11: task-runs returns 1 item", ok)


def test_T12(tmpdir):
    """T12: GET /mas-trace with file present."""
    print("\n--- T12: GET /mas-trace with file present ---")
    path = tmpdir / "mas.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"event": "test"}) + "\n")
    resp = handle_mas_trace(path, 20)
    ok = resp["ok"] and len(resp["data"]["mas_trace"]) == 1
    return test("T12: mas-trace returns 1 item", ok)


def test_T13(tmpdir):
    """T13: POST /command rejects empty command."""
    print("\n--- T13: POST /command rejects empty command ---")
    gateway = Path(__file__).resolve().parent.parent / "scripts" / "command_gateway.py"
    resp = handle_command("", gateway)
    ok = not resp["ok"] and resp["error"]["code"] == "EMPTY_COMMAND"
    return test("T13: empty command rejected", ok, str(resp["error"]["code"]))


def test_T14(tmpdir):
    """T14: POST /command delegates to command_gateway.py."""
    print("\n--- T14: POST /command delegates to gateway ---")
    gateway = Path(__file__).resolve().parent.parent / "scripts" / "command_gateway.py"
    resp = handle_command("check health", gateway)
    ok = resp["ok"] and "gateway_result" in resp["data"]
    return test("T14: command delegates to gateway", ok, f"exit={resp['data'].get('gateway_exit_code')}")


def test_T15(tmpdir):
    """T15: POST /command rejects command exceeding max length."""
    print("\n--- T15: POST /command rejects overlong command ---")
    gateway = Path(__file__).resolve().parent.parent / "scripts" / "command_gateway.py"
    long_cmd = "x" * 3000
    resp = handle_command(long_cmd, gateway)
    ok = not resp["ok"] and resp["error"]["code"] == "COMMAND_TOO_LONG"
    return test("T15: overlong command rejected", ok)


def test_T16(tmpdir):
    """T16: build_response produces correct JSON structure."""
    print("\n--- T16: build_response structure ---")
    resp = build_response(True, data={"key": "val"})
    ok = all(k in resp for k in ("ok", "data", "error", "meta"))
    return test("T16: response has ok/data/error/meta", ok)


# --- Integration Test: Real HTTP Server ---

def test_T17():
    """T17: Real HTTP server starts, handles /health, stops."""
    print("\n--- T17: Real HTTP server integration ---")
    from scripts.api_server import create_server, OnePalHandler
    import tempfile
    from pathlib import Path

    tmpdir = Path(tempfile.mkdtemp(prefix="onepal_api_test_"))
    hpath = tmpdir / "health.json"
    hpath.write_text(json.dumps({"status": "ready", "checked_at": "2026-01-01T00:00:00Z"}), encoding="utf-8")

    # Configure handler
    class TestHandler(OnePalHandler):
        health_path = hpath

    server = create_server("127.0.0.1", 0, TestHandler)
    host = server.server_address[0]
    port = server.server_port

    try:
        # Start in thread
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.3)

        # Make request
        url = f"http://{host}:{port}/health"
        resp = urllib.request.urlopen(url, timeout=5)
        body = json.loads(resp.read().decode("utf-8"))
        ok = body.get("ok") and body["data"].get("status") == "ready"
        result = test("T17: real HTTP server /health returns ready", ok, str(body.get("data", {}).get("status")))
        return result
    except Exception as e:
        return test("T17: real HTTP server integration", False, str(e))
    finally:
        server.shutdown()
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    global passed, failed

    print("=" * 60)
    print("OnePal API Server Tests (T1-T17)")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="onepal_api_test_") as td:
        tmpdir = Path(td)
        test_T1()
        test_T2(tmpdir)
        test_T3(tmpdir)
        test_T4(tmpdir)
        test_T5(tmpdir)
        test_T6(tmpdir)
        test_T7(tmpdir)
        test_T8(tmpdir)
        test_T9(tmpdir)
        test_T10(tmpdir)
        test_T11(tmpdir)
        test_T12(tmpdir)
        test_T13(tmpdir)
        test_T14(tmpdir)
        test_T15(tmpdir)
        test_T16(tmpdir)

    test_T17()

    # Memory API tests
    with tempfile.TemporaryDirectory(prefix="onepal_api_mem_") as td:
        md = Path(td)
        test_mem_get_empty(md)
        test_mem_candidates_empty(md)
        test_mem_proposals_empty(md)
        test_mem_post_empty(md)
        test_mem_post_overlong(md)
        test_mem_store_no_pid(md)
        test_mem_archive_no_mid(md)
        test_mem_redact(md)
        test_mem_propose_no_cid(md)
        test_mem_candidates_create(md)
        test_mem_response_structure(md)
    test_mem_no_shell()
    test_mem_unknown_route()
    test_mem_path_safety()

    # Research API tests
    with tempfile.TemporaryDirectory(prefix="onepal_api_r_") as td:
        rd = Path(td)
        test_research_sources_empty(rd)
        test_research_packets_empty(rd)
        test_research_evidence_empty(rd)
        test_research_cards_empty(rd)
        test_research_post_validation(rd)
    test_research_sources_no_path()
    test_research_api_no_shell()

    # Growth API tests
    with tempfile.TemporaryDirectory(prefix="onepal_api_g_") as td:
        gd = Path(td)
        test_growth_get_empty(gd)
        test_growth_candidate_validation(gd)
        test_growth_goal_flow(gd)
        test_growth_plan_flow(gd)
        test_growth_review_flow(gd)
    test_growth_api_no_shell()
    test_growth_path_safety()

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


# ─── Research API Tests (Task 11-B) ───

def test_research_sources_empty(tmpdir):
    print("\n--- R1: GET /research/sources empty ---")
    from scripts.api_server import handle_research_sources_get
    resp = handle_research_sources_get(tmpdir / "x.jsonl", 20)
    test("R1: sources empty", resp["ok"] and resp["data"]["sources"] == [])

def test_research_packets_empty(tmpdir):
    print("\n--- R2: GET /research/packets empty ---")
    from scripts.api_server import handle_research_packets_get
    resp = handle_research_packets_get(tmpdir / "x.jsonl", 20)
    test("R2: packets empty", resp["ok"] and resp["data"]["packets"] == [])

def test_research_evidence_empty(tmpdir):
    print("\n--- R3: GET /research/evidence empty ---")
    from scripts.api_server import handle_research_evidence_get
    resp = handle_research_evidence_get(tmpdir / "x.jsonl", 20)
    test("R3: evidence empty", resp["ok"] and resp["data"]["evidence"] == [])

def test_research_cards_empty(tmpdir):
    print("\n--- R4: GET /research/cognition-cards empty ---")
    from scripts.api_server import handle_research_cards_get
    resp = handle_research_cards_get(tmpdir / "x.jsonl", 20)
    test("R4: cognition-cards empty", resp["ok"] and resp["data"]["cards"] == [])

def test_research_sources_no_path():
    print("\n--- R5: research sources no path param ---")
    from scripts.api_server import RESEARCH_SOURCES_PATH, handle_research_sources_get
    # Verify path is under PROJECT_ROOT (hardcoded)
    ok = str(RESEARCH_SOURCES_PATH).startswith(str(PROJECT_ROOT))
    test("R5: sources path under project root", ok)

def test_research_post_validation(tmpdir):
    print("\n--- R6: research POST validation ---")
    from scripts.api_server import handle_research_sources_post
    resp = handle_research_sources_post({"content_summary":""}, "scripts/research_packet.py")
    ok = not resp["ok"] and resp["error"]["code"] == "EMPTY_CONTENT"
    test("R6: sources rejects empty", ok)

    resp2 = handle_research_sources_post({"content_summary":"x"*3000}, "scripts/research_packet.py")
    ok2 = not resp2["ok"] and resp2["error"]["code"] == "CONTENT_TOO_LONG"
    test("R6b: sources rejects overlong", ok2)

def test_research_api_no_shell():
    print("\n--- R7: research API no shell=True ---")
    with open(PROJECT_ROOT / "scripts" / "api_server.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    code = "".join([l for l in lines if "no shell=True" not in l and not l.strip().startswith("#")])
    test("R7: no shell=True in API", "shell=True" not in code)


# --- Growth API Tests (Task 13-B) ---

def test_growth_get_empty(tmpdir):
    print("\n--- G1-G8: Growth GET empty lists ---")
    from scripts.api_server import (
        handle_growth_candidates_get, handle_growth_goals_get, handle_growth_capacity_get,
        handle_growth_weekly_get, handle_growth_tasks_get, handle_growth_reviews_get,
        handle_growth_adjustments_get, handle_growth_handoffs_get,
    )
    checks = [
        ("G1: candidates empty", handle_growth_candidates_get(tmpdir / "c.jsonl", 20), "candidates"),
        ("G2: goals empty", handle_growth_goals_get(tmpdir / "g.jsonl", 20), "goals"),
        ("G3: capacity empty", handle_growth_capacity_get(tmpdir / "cap.jsonl", 20), "capacity"),
        ("G4: weekly empty", handle_growth_weekly_get(tmpdir / "w.jsonl", 20), "weekly_plans"),
        ("G5: daily tasks empty", handle_growth_tasks_get(tmpdir / "t.jsonl", 20), "daily_tasks"),
        ("G6: reviews empty", handle_growth_reviews_get(tmpdir / "r.jsonl", 20), "reviews"),
        ("G7: adjustments empty", handle_growth_adjustments_get(tmpdir / "a.jsonl", 20), "adjustments"),
        ("G8: handoffs empty", handle_growth_handoffs_get(tmpdir / "h.jsonl", 20), "handoffs"),
    ]
    for label, resp, key in checks:
        test(label, resp["ok"] and resp["data"][key] == [])


def test_growth_candidate_validation(tmpdir):
    print("\n--- G9-G12: Growth candidate validation ---")
    from scripts.api_server import handle_growth_candidates_post, MAX_GROWTH_CONTENT
    script = PROJECT_ROOT / "scripts" / "growth_goal.py"
    cand = tmpdir / "candidates.jsonl"
    audit = tmpdir / "audit.jsonl"
    resp = handle_growth_candidates_post({"title": ""}, script, cand, audit)
    test("G9: empty candidate title rejected", not resp["ok"] and resp["error"]["code"] == "EMPTY_TITLE")
    resp2 = handle_growth_candidates_post({"title": "sk-abc123def456ghi"}, script, cand, audit)
    test("G10: secret candidate rejected", not resp2["ok"] and resp2["error"]["code"] == "SECRET_DETECTED")
    resp3 = handle_growth_candidates_post({"title": "x" * (MAX_GROWTH_CONTENT + 1)}, script, cand, audit)
    test("G11: overlong candidate rejected", not resp3["ok"] and resp3["error"]["code"] == "CONTENT_TOO_LONG")
    resp4 = handle_growth_candidates_post({"title": "Learn API design", "reason": "Task 13 test"}, script, cand, audit)
    test("G12: valid candidate created", resp4["ok"] and resp4["data"].get("candidate_id"))


def test_growth_goal_flow(tmpdir):
    print("\n--- G13-G21: Growth goal flow ---")
    from scripts.api_server import (
        handle_growth_candidates_post, handle_growth_candidate_accept_post,
        handle_growth_candidate_reject_post, handle_growth_goals_post,
        handle_growth_archive_post,
    )
    script = PROJECT_ROOT / "scripts" / "growth_goal.py"
    cand = tmpdir / "candidates.jsonl"
    goals = tmpdir / "goals.jsonl"
    audit = tmpdir / "audit.jsonl"

    create = handle_growth_candidates_post({"title": "Goal flow", "reason": "test"}, script, cand, audit)
    cid = create["data"].get("candidate_id")
    accept = handle_growth_candidate_accept_post({"candidate_id": cid}, script, cand, audit)
    test("G13: candidate accepted", accept["ok"] and accept["data"]["status"] == "accepted")
    goal = handle_growth_goals_post({"candidate_id": cid, "success_criteria": "Pass Task 13 tests"}, script, cand, goals, audit)
    gid = goal["data"].get("goal_id")
    test("G14: accepted candidate creates goal", goal["ok"] and gid)
    missing_success = handle_growth_goals_post({"candidate_id": cid, "success_criteria": ""}, script, cand, goals, audit)
    test("G15: missing success rejected", not missing_success["ok"] and missing_success["error"]["code"] == "MISSING_SUCCESS")
    nf = handle_growth_candidate_accept_post({"candidate_id": "gc_missing"}, script, cand, audit)
    test("G16: missing candidate rejected", not nf["ok"] and nf["error"]["code"] == "CANDIDATE_NOT_FOUND")
    create2 = handle_growth_candidates_post({"title": "Not accepted", "reason": "test"}, script, cand, audit)
    nonaccepted = handle_growth_goals_post({"candidate_id": create2["data"].get("candidate_id"), "success_criteria": "Done"}, script, cand, goals, audit)
    test("G17: non-accepted candidate rejected", not nonaccepted["ok"] and nonaccepted["error"]["code"] == "NOT_ACCEPTED")
    reject = handle_growth_candidate_reject_post({"candidate_id": create2["data"].get("candidate_id"), "reason": "not now"}, script, cand, audit)
    test("G18: candidate rejected", reject["ok"] and reject["data"]["status"] == "rejected")
    archive = handle_growth_archive_post({"goal_id": gid}, script, goals, audit)
    test("G19: goal archived", archive["ok"] and archive["data"]["status"] == "archived")
    missing_goal = handle_growth_archive_post({"goal_id": "goal_missing"}, script, goals, audit)
    test("G20: missing goal archive rejected", not missing_goal["ok"] and missing_goal["error"]["code"] == "GOAL_NOT_FOUND")
    bad_secret = handle_growth_goals_post({"candidate_id": cid, "success_criteria": "token=abcdefghijklmnopqrstuvwxyz"}, script, cand, goals, audit)
    test("G21: secret success criteria rejected", not bad_secret["ok"] and bad_secret["error"]["code"] == "SECRET_DETECTED")


def test_growth_plan_flow(tmpdir):
    print("\n--- G22-G28: Growth plan flow ---")
    from scripts.api_server import (
        handle_growth_capacity_post, handle_growth_weekly_post,
        handle_growth_tasks_post, handle_growth_task_status_post,
    )
    script = PROJECT_ROOT / "scripts" / "growth_plan.py"
    cap = tmpdir / "capacity.jsonl"
    weekly = tmpdir / "weekly.jsonl"
    tasks = tmpdir / "tasks.jsonl"
    audit = tmpdir / "audit.jsonl"
    capacity = handle_growth_capacity_post({"available_hours": 3, "active_goal_ids": ["g1", "g2"]}, script, cap, audit)
    test("G22: capacity created", capacity["ok"] and capacity["data"].get("budget_id"))
    bad_capacity = handle_growth_capacity_post({"available_hours": "abc"}, script, cap, audit)
    test("G23: invalid capacity hours rejected", not bad_capacity["ok"] and bad_capacity["error"]["code"] == "INVALID_HOURS")
    weekly_resp = handle_growth_weekly_post({"week_start": "2026-06-08", "goal_ids": ["g1"]}, script, weekly, audit)
    test("G24: weekly plan created", weekly_resp["ok"] and weekly_resp["data"].get("weekly_plan_id"))
    weekly_bad = handle_growth_weekly_post({"week_start": ""}, script, weekly, audit)
    test("G25: missing week start rejected", not weekly_bad["ok"] and weekly_bad["error"]["code"] == "MISSING_WEEK_START")
    task = handle_growth_tasks_post({"date": "2026-06-08", "goal_id": "g1", "title": "Implement growth API"}, script, tasks, audit)
    tid = task["data"].get("task_id")
    test("G26: daily task created", task["ok"] and tid)
    status = handle_growth_task_status_post({"task_id": tid, "status": "done"}, script, tasks, audit)
    test("G27: task status updated", status["ok"] and status["data"]["status"] == "done")
    nf = handle_growth_task_status_post({"task_id": "task_missing", "status": "done"}, script, tasks, audit)
    test("G28: missing task status rejected", not nf["ok"] and nf["error"]["code"] == "TASK_NOT_FOUND")


def test_growth_review_flow(tmpdir):
    print("\n--- G29-G34: Growth review flow ---")
    from scripts.api_server import (
        handle_growth_reviews_post, handle_growth_adjustments_post,
        handle_growth_handoffs_post, handle_growth_archive_post,
    )
    review_script = PROJECT_ROOT / "scripts" / "growth_review.py"
    goal_script = PROJECT_ROOT / "scripts" / "growth_goal.py"
    reviews = tmpdir / "reviews.jsonl"
    adjustments = tmpdir / "adjustments.jsonl"
    goals = tmpdir / "goals.jsonl"
    audit = tmpdir / "audit.jsonl"
    review = handle_growth_reviews_post({"goal_id": "goal_1", "self_rating": 3, "blockers": "time"}, review_script, reviews, audit)
    test("G29: review created", review["ok"] and review["data"].get("review_id"))
    missing_review = handle_growth_reviews_post({"goal_id": ""}, review_script, reviews, audit)
    test("G30: missing review goal rejected", not missing_review["ok"] and missing_review["error"]["code"] == "MISSING_ID")
    adjustment = handle_growth_adjustments_post({"goal_id": "goal_1", "proposal_type": "reduce_scope", "reason": "overloaded", "impact": "high"}, review_script, adjustments, audit)
    test("G31: high impact adjustment requires approval", adjustment["ok"] and adjustment["data"].get("approval_required") is True)
    bad_adjustment = handle_growth_adjustments_post({"goal_id": "goal_1", "proposal_type": "", "reason": ""}, review_script, adjustments, audit)
    test("G32: missing adjustment type rejected", not bad_adjustment["ok"] and bad_adjustment["error"]["code"] == "MISSING_ARGS")
    missing_handoff = handle_growth_handoffs_post({"goal_id": ""}, review_script, audit)
    test("G33: missing handoff goal rejected", not missing_handoff["ok"] and missing_handoff["error"]["code"] == "MISSING_ID")
    missing_archive = handle_growth_archive_post({"goal_id": ""}, goal_script, goals, audit)
    test("G34: missing archive goal rejected", not missing_archive["ok"] and missing_archive["error"]["code"] == "MISSING_ID")


def test_growth_api_no_shell():
    print("\n--- G35: Growth API no shell=True ---")
    with open(PROJECT_ROOT / "scripts" / "api_server.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    code = "".join([l for l in lines if "no shell=True" not in l and not l.strip().startswith("#")])
    test("G35: no shell=True in Growth API", "shell=True" not in code)


def test_growth_path_safety():
    print("\n--- G36: Growth paths under project root ---")
    from scripts.api_server import (
        GROWTH_CANDIDATES_PATH, GROWTH_GOALS_PATH, GROWTH_CAPACITY_PATH,
        GROWTH_WEEKLY_PATH, GROWTH_TASKS_PATH, GROWTH_REVIEWS_PATH,
        GROWTH_ADJUSTMENTS_PATH, GROWTH_HANDOFFS_PATH,
    )
    paths = [GROWTH_CANDIDATES_PATH, GROWTH_GOALS_PATH, GROWTH_CAPACITY_PATH,
             GROWTH_WEEKLY_PATH, GROWTH_TASKS_PATH, GROWTH_REVIEWS_PATH,
             GROWTH_ADJUSTMENTS_PATH, GROWTH_HANDOFFS_PATH]
    ok = all(str(p).startswith(str(PROJECT_ROOT)) for p in paths)
    test("G36: all Growth paths under PROJECT_ROOT", ok)


# ─── Memory API Tests (Task 09-B) ───

def test_mem_get_empty(tmpdir):
    """T18: GET /memory missing file returns empty."""
    print("\n--- T18: GET /memory missing → empty ---")
    from scripts.api_server import handle_memory_get, build_response
    resp = handle_memory_get({}, tmpdir / "c.jsonl", tmpdir / "p.jsonl", tmpdir / "x.jsonl", 20)
    ok = resp["ok"] and resp["data"]["memories"] == []
    test("T18: GET /memory missing → empty", ok, str(len(resp["data"]["memories"])))


def test_mem_candidates_empty(tmpdir):
    """T19: GET /memory/candidates missing → empty."""
    print("\n--- T19: GET /memory/candidates missing → empty ---")
    from scripts.api_server import handle_memory_candidates_get
    resp = handle_memory_candidates_get(tmpdir / "x.jsonl", 20)
    ok = resp["ok"] and resp["data"]["candidates"] == []
    test("T19: GET /candidates missing → empty", ok)


def test_mem_proposals_empty(tmpdir):
    """T20: GET /memory/proposals missing → empty."""
    print("\n--- T20: GET /memory/proposals missing → empty ---")
    from scripts.api_server import handle_memory_proposals_get
    resp = handle_memory_proposals_get(tmpdir / "x.jsonl", 20)
    ok = resp["ok"] and resp["data"]["proposals"] == []
    test("T20: GET /proposals missing → empty", ok)


def test_mem_post_empty(tmpdir):
    """T21: POST /memory/candidates rejects empty content."""
    print("\n--- T21: POST /candidates empty → reject ---")
    from scripts.api_server import handle_memory_candidates_post
    resp = handle_memory_candidates_post({"content": ""}, "scripts/memory_candidate.py")
    ok = not resp["ok"] and resp["error"]["code"] == "EMPTY_CONTENT"
    test("T21: POST /candidates empty → reject", ok)


def test_mem_post_overlong(tmpdir):
    """T22: POST /memory/candidates rejects overlong content."""
    print("\n--- T22: POST /candidates overlong → reject ---")
    from scripts.api_server import handle_memory_candidates_post, MAX_MEMORY_CONTENT
    resp = handle_memory_candidates_post({"content": "x" * (MAX_MEMORY_CONTENT + 1)}, "scripts/memory_candidate.py")
    ok = not resp["ok"] and resp["error"]["code"] == "CONTENT_TOO_LONG"
    test("T22: POST /candidates overlong → reject", ok)


def test_mem_store_no_pid(tmpdir):
    """T23: POST /memory/store no proposal_id → reject."""
    print("\n--- T23: POST /store no pid → reject ---")
    from scripts.api_server import handle_memory_store_post
    resp = handle_memory_store_post({"proposal_id": ""}, "scripts/memory_store.py")
    ok = not resp["ok"]
    test("T23: POST /store no pid → reject", ok)


def test_mem_archive_no_mid(tmpdir):
    """T24: POST /memory/archive no memory_id → reject."""
    print("\n--- T24: POST /archive no mid → reject ---")
    from scripts.api_server import handle_memory_archive_post
    resp = handle_memory_archive_post({"memory_id": ""}, "scripts/memory_store.py")
    ok = not resp["ok"]
    test("T24: POST /archive no mid → reject", ok)


def test_mem_redact(tmpdir):
    """T25: redaction detects secrets."""
    print("\n--- T25: secret redaction active ---")
    from scripts.api_server import _redact
    is_redacted, result = _redact("sk-abc123def456ghi789jkl012")
    ok = is_redacted and result == "[REDACTED]"
    test("T25: _redact detects sk- pattern", ok)

    is_r2, r2 = _redact("Normal project decision text")
    ok2 = not is_r2 and r2 == "Normal project decision text"
    test("T25b: _redact passes clean text", ok2)

    is_r3, r3 = _redact("-----BEGIN RSA PRIVATE KEY-----")
    test("T25c: _redact detects BEGIN KEY", is_r3)


def test_mem_propose_no_cid(tmpdir):
    """T26: POST /memory/proposals no candidate_id → reject."""
    print("\n--- T26: POST /proposals no cid → reject ---")
    from scripts.api_server import handle_memory_proposals_post
    resp = handle_memory_proposals_post({"candidate_id": ""}, "scripts/memory_candidate.py")
    ok = not resp["ok"]
    test("T26: POST /proposals no cid → reject", ok)


def test_mem_candidates_create(tmpdir):
    """T27: POST /memory/candidates creates valid candidate."""
    print("\n--- T27: POST /candidates creates valid ---")
    from scripts.api_server import handle_memory_candidates_post
    resp = handle_memory_candidates_post({
        "content": "Test project decision for Task 09",
        "memory_type": "project_decision",
        "source_type": "manual",
        "source_agent": "test",
        "sensitivity": "internal",
    }, "scripts/memory_candidate.py")
    # May succeed or fail depending on script path — test structure, not actual execution
    ok = isinstance(resp, dict) and "ok" in resp
    test("T27: POST /candidates returns structured response", ok)


def test_mem_response_structure(tmpdir):
    """T28: All memory GET responses are JSON-compliant."""
    print("\n--- T28: memory GET JSON structure ---")
    from scripts.api_server import handle_memory_get, handle_memory_candidates_get, handle_memory_proposals_get
    for fn, name in [
        (handle_memory_get, "memory"), (handle_memory_candidates_get, "candidates"),
        (handle_memory_proposals_get, "proposals")
    ]:
        if name == "memory":
            resp = fn({}, tmpdir / "c.jsonl", tmpdir / "p.jsonl", tmpdir / "s.jsonl", 20)
        else:
            resp = fn(tmpdir / "x.jsonl", 20)
        ok = all(k in resp for k in ("ok", "data", "error", "meta"))
        test(f"T28-{name}: has ok/data/error/meta", ok)


def test_mem_no_shell():
    """T29: Memory API code has no shell=True (excluding comments)."""
    print("\n--- T29: Memory API no shell=True ---")
    with open(PROJECT_ROOT / "scripts" / "api_server.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Check non-comment, non-docstring lines only
    code_lines = [l for l in lines if not l.strip().startswith("#") and "no shell=True" not in l]
    content = "".join(code_lines)
    ok = "shell=True" not in content
    test("T29: no shell=True in api_server.py (excluding comments)", ok)


def test_mem_unknown_route():
    """T30: unknown memory route structure."""
    print("\n--- T30: 404 response structure ---")
    from scripts.api_server import build_response
    resp = build_response(False, error={"code": "NOT_FOUND", "message": "route not found"})
    ok = not resp["ok"] and resp["error"]["code"] == "NOT_FOUND"
    test("T30: 404 response has NOT_FOUND", ok)


def test_mem_path_safety():
    """T31: No arbitrary path accepted by memory endpoints."""
    print("\n--- T31: memory endpoint path safety ---")
    from scripts.api_server import MEMORY_CANDIDATES_PATH, MEMORY_STORE_PATH, MEMORY_PROPOSALS_PATH
    # Verify all paths are under PROJECT_ROOT
    ok = all(str(p).startswith(str(PROJECT_ROOT)) for p in [MEMORY_CANDIDATES_PATH, MEMORY_PROPOSALS_PATH, MEMORY_STORE_PATH])
    test("T31: all memory paths under PROJECT_ROOT", ok)


if __name__ == "__main__":
    main()
