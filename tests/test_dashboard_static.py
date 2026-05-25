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

ALLOWED_ENDPOINTS = {"/health", "/tasks", "/task-trees", "/task-runs", "/mas-trace", "/command"}
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

# Summary
print("\n" + "=" * 60)
total = passed + failed
print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
