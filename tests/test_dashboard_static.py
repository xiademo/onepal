#!/usr/bin/env python3
"""OnePal Dashboard Static Tests - Task 07-B (T1-T18)

Verifies dashboard files exist, have no external deps, no dangerous code,
and reference only allowed API endpoints.

Usage: py tests/test_dashboard_static.py
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = PROJECT_ROOT / "dashboard"
INDEX = DASHBOARD / "index.html"
APP = DASHBOARD / "app.js"
CSS = DASHBOARD / "style.css"

ALLOWED_ENDPOINTS = {
    "/health", "/tasks", "/task-trees", "/task-runs", "/mas-trace", "/command",
    "/growth/candidates", "/growth/candidates/accept", "/growth/candidates/reject",
    "/growth/goals", "/growth/capacity", "/growth/weekly-plans",
    "/growth/daily-tasks", "/growth/daily-tasks/status", "/growth/reviews",
    "/growth/adjustments", "/growth/handoffs", "/growth/archive",
}
FORBIDDEN_PATTERNS = [
    "runtime/", "logs/", "command_gateway.py", "runtime_runner.py",
    "request_action.py", "check_permission.py", "decide_proposal.py",
    "eval(", "new Function(", "child_process", "require(", "fs.",
    "shell=True", "os.system", "popen",
]
DANGEROUS_PATTERNS = ["eval(", "new Function(", "child_process", "require("]

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


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# T1-T3: File existence
print("\n--- T1-T3: File existence ---")
test("T1: dashboard/index.html exists", INDEX.exists())
test("T2: dashboard/app.js exists", APP.exists())
test("T3: dashboard/style.css exists", CSS.exists())

if not INDEX.exists():
    print("Missing index.html — cannot continue")
    sys.exit(1)

html = read_file(INDEX)
js = read_file(APP) if APP.exists() else ""
css = read_file(CSS) if CSS.exists() else ""

# T4: No external CDN
print("\n--- T4: No external CDN ---")
cdn_pattern = r'https?://(?!127\.0\.0\.1|localhost)[^\s"\']+'
cdn_matches = re.findall(cdn_pattern, html + js + css)
ok = len(cdn_matches) == 0
test("T4: no external CDN/URLs", ok, f"found: {cdn_matches[:5]}" if cdn_matches else "")

# T5: No npm/package/node_modules references
print("\n--- T5: No npm/package dependency refs ---")
npm_refs = re.findall(r'(package\.json|node_modules|npm\s|npx\s)', html + js + css)
test("T5: no npm/package/node_modules refs", len(npm_refs) == 0, str(npm_refs) if npm_refs else "")

# T6: index.html references app.js and style.css correctly
print("\n--- T6: index.html references correct files ---")
ok_js = 'src="app.js"' in html
ok_css = 'href="style.css"' in html
test("T6: index.html references app.js and style.css", ok_js and ok_css)

# T7: app.js only fetches allowed endpoints
print("\n--- T7: app.js only fetches allowed endpoints ---")
fetch_urls = re.findall(r"API_BASE\s*\+\s*['\"]([^'\"]+)", js)
all_allowed = all(u in ALLOWED_ENDPOINTS for u in fetch_urls)
test("T7: only allowed API endpoints in fetch", all_allowed,
     f"found: {fetch_urls}, allowed: {ALLOWED_ENDPOINTS}")

# T8-T13: Specific endpoint usage
print("\n--- T8-T13: Specific endpoint references ---")
ep_checks = {
    "T8: GET /health": "/health",
    "T9: GET /tasks": "/tasks",
    "T10: GET /task-trees": "/task-trees",
    "T11: GET /task-runs": "/task-runs",
    "T12: GET /mas-trace": "/mas-trace",
    "T13: POST /command": "/command",
}
for label, ep in ep_checks.items():
    test(label, (API_BASE_ref := 'API_BASE + "' + ep + '"') in js or
          (ep in js and 'API_BASE' in js),
          f"looking for {API_BASE_ref}")

# T14: No runtime/ or logs/ direct access
print("\n--- T14: No runtime/logs direct access ---")
runtime_refs = re.findall(r'runtime/', js)
logs_refs = re.findall(r'logs/', js)
test("T14: no runtime/ or logs/ in app.js", len(runtime_refs) == 0 and len(logs_refs) == 0)

# T15: No direct script references
print("\n--- T15: No direct gateway/runner/action references ---")
script_refs = re.findall(r'(command_gateway\.py|runtime_runner\.py|request_action\.py|check_permission\.py|decide_proposal\.py)', js)
test("T15: no direct script references", len(script_refs) == 0, str(script_refs) if script_refs else "")

# T16: No eval/new Function/require/fs/child_process (exclude comments)
print("\n--- T16: No dangerous JS patterns ---")
# Strip single-line comments and multi-line comments before checking
js_stripped = re.sub(r'//.*$', '', js, flags=re.MULTILINE)
js_stripped = re.sub(r'/\*.*?\*/', '', js_stripped, flags=re.DOTALL)
danger_found = []
for pat in DANGEROUS_PATTERNS:
    if pat in js_stripped:
        danger_found.append(pat)
test("T16: no eval/new Function/require/fs/child_process", len(danger_found) == 0, str(danger_found))

# T17: index.html contains 5 core panels
print("\n--- T17: index.html contains 5 core panels ---")
panel_ids = ["health-panel", "command-panel", "tasks-panel", "runs-panel", "trace-panel"]
all_panels = all(f'id="{pid}"' in html for pid in panel_ids)
test("T17: all 5 core panels in index.html", all_panels,
     "missing: " + str([p for p in panel_ids if f'id="{p}"' not in html]))

# T18: style.css has no external @import
print("\n--- T18: style.css has no external @import ---")
import_refs = re.findall(r'@import\s+url\(["\']?https?://', css)
test("T18: no external @import in style.css", len(import_refs) == 0)

# ─── Memory Panel Tests (Task 09-B) ───
print("\n--- T19-T32: Memory Panel static checks ---")
test("T19: index.html contains memory-panel", 'id="memory-panel"' in html)
test("T20: index.html memory-panel DOM id", 'memory-panel' in html)

TEST_ENDPOINTS_JS = [
    ("T21: app.js GET /memory", "/memory"),
    ("T22: app.js GET /memory/candidates", "/memory/candidates"),
    ("T23: app.js GET /memory/proposals", "/memory/proposals"),
    ("T24: app.js POST /memory/candidates", "/memory/candidates"),
    ("T25: app.js POST /memory/proposals", "/memory/proposals"),
    ("T26: app.js POST /memory/store", "/memory/store"),
    ("T27: app.js POST /memory/archive", "/memory/archive"),
]
for label, ep in TEST_ENDPOINTS_JS:
    test(label, ep in js)

test("T28: app.js no direct memory/ access", 
     "memory/" not in js or 'apiPost("/memory' in js or "apiPost('/memory" in js)
test("T29: app.js no memory_candidate.py direct call", "memory_candidate.py" not in js)
test("T30: app.js no memory_store.py direct call", "memory_store.py" not in js)
test("T31: app.js no eval/new Function", "eval(" not in js_stripped and "new Function(" not in js_stripped)
test("T32: app.js no require/fs/child_process", "require(" not in js and re.search(r"\bfs\s*\.", js) is None)

# ─── Research Panel Tests (Task 11-B) ───
print("\n--- T33-T42: Research Panel static checks ---")
test("T33: index.html contains research-panel", 'id="research-panel"' in html)
test("T34: research-panel DOM id", 'research-panel' in html)
for label, ep in [
    ("T35: app.js GET /research/sources", "/research/sources"),
    ("T36: app.js GET /research/packets", "/research/packets"),
    ("T37: app.js GET /research/cognition-cards", "/research/cognition-cards"),
    ("T38: app.js POST /research/sources", "/research/sources"),
]:
    test(label, ep in js)
test("T39: app.js no research/ direct access", "research/" not in js or "apiPost('/research" in js or 'apiGet("/research' in js)
test("T40: app.js no research_packet.py call", "research_packet.py" not in js)
test("T41: app.js no cognition_card.py call", "cognition_card.py" not in js)
test("T42: app.js fetch uses research endpoints", "/research/sources" in js or "/research/packets" in js)

# Growth Panel Tests (Task 13-B)
print("\n--- T43-T64: Growth Panel static checks ---")
test("T43: index.html contains growth-panel", 'id="growth-panel"' in html)
test("T44: index.html growth refresh button", 'id="growth-refresh-btn"' in html)
panel_count = len(re.findall(r'<section class="panel ', html))
test("T45: index.html contains 8 panels", panel_count == 8, f"panels={panel_count}")
test("T46: style.css growth panel full width", ".growth-panel" in css and "grid-column: 1 / -1" in css)
test("T47: growth panel appears after research panel", html.find('id="research-panel"') < html.find('id="growth-panel"'))
for label, ep in [
    ("T48: app.js GET /growth/candidates", "/growth/candidates"),
    ("T49: app.js GET /growth/goals", "/growth/goals"),
    ("T50: app.js GET /growth/capacity", "/growth/capacity"),
    ("T51: app.js GET /growth/weekly-plans", "/growth/weekly-plans"),
    ("T52: app.js GET /growth/daily-tasks", "/growth/daily-tasks"),
    ("T53: app.js GET /growth/reviews", "/growth/reviews"),
    ("T54: app.js GET /growth/adjustments", "/growth/adjustments"),
    ("T55: app.js GET /growth/handoffs", "/growth/handoffs"),
    ("T56: app.js POST /growth/candidates", "/growth/candidates"),
    ("T57: app.js POST /growth/candidates/accept", "/growth/candidates/accept"),
]:
    test(label, ep in js)
test("T58: app.js no direct growth/ file access",
     "growth/" not in js or "apiPost('/growth" in js or "apiGet('/growth" in js)
test("T59: app.js no growth_goal.py call", "growth_goal.py" not in js)
test("T60: app.js no growth_plan.py call", "growth_plan.py" not in js)
test("T61: app.js no growth_review.py call", "growth_review.py" not in js)
test("T62: app.js no memory store write from growth", "/memory/store" not in js[js.find("Growth Center Panel"):])
test("T63: app.js growth create form ids", "growth-title" in js and "growth-area" in js and "growth-reason" in js)
test("T64: app.js no dangerous growth patterns", "eval(" not in js_stripped and "new Function(" not in js_stripped and "child_process" not in js)

# Summary
print("\n" + "=" * 60)
total = passed + failed
print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
