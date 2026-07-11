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
    "/memory", "/memory/candidates", "/memory/proposals", "/memory/store", "/memory/archive",
    "/memory/reviews", "/memory/conflicts", "/memory/changes", "/memory/snapshots",
    "/research/sources", "/research/packets", "/research/evidence",
    "/research/cognition-cards", "/research/handoffs", "/research/archive",
    "/growth/candidates", "/growth/candidates/accept", "/growth/candidates/reject",
    "/growth/goals", "/growth/capacity", "/growth/weekly-plans",
    "/growth/daily-tasks", "/growth/daily-tasks/status", "/growth/reviews",
    "/growth/adjustments", "/growth/handoffs", "/growth/archive",
    "/career/assets", "/career/claims", "/career/jds", "/career/evaluations",
    "/career/applications", "/career/handoffs",
    "/automation/workflows", "/automation/runs",
    "/skills/candidates", "/skills/reviews",
    "/knowledge/nodes", "/knowledge/edges", "/knowledge/boundaries", "/knowledge/state",
    "/model/routes", "/model/cost-events", "/model/provider", "/model/provider/test", "/assistant/proposals",
    "/mcp/profiles", "/mcp/tool-policies",
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
cdn_pattern = r'(?:src|href)=["\'](https?://(?!127\.0\.0\.1|localhost)[^"\']+)'
cdn_matches = re.findall(cdn_pattern, html)
cdn_matches = [match[0] for match in cdn_matches]
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
test("T45: index.html contains 15 panels", panel_count == 15, f"panels={panel_count}")
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

# Memory Governance Tests (Task 14-B)
print("\n--- T65-T77: Memory Governance static checks ---")
for label, ep in [
    ("T65: app.js GET /memory/reviews", "/memory/reviews"),
    ("T66: app.js GET /memory/conflicts", "/memory/conflicts"),
    ("T67: app.js GET /memory/changes", "/memory/changes"),
    ("T68: app.js GET /memory/snapshots", "/memory/snapshots"),
    ("T69: app.js POST /memory/reviews", "/memory/reviews"),
    ("T70: app.js POST /memory/conflicts", "/memory/conflicts"),
    ("T71: app.js POST /memory/snapshots", "/memory/snapshots"),
]:
    test(label, ep in js)
test("T72: Memory panel shows Quality Reviews", "Quality Reviews" in js)
test("T73: Memory panel shows Conflicts", "Conflicts" in js)
test("T74: Memory panel shows Change Requests", "Change Requests" in js)
test("T75: Memory panel shows Snapshots", "Snapshots" in js)
test("T76: app.js no memory_governance.py direct call", "memory_governance.py" not in js)
test("T77: memory governance uses API only",
     "memory/reviews/" not in js and "memory/conflicts/" not in js and "memory/changes/" not in js and "memory/snapshots/" not in js)

# Career Panel Tests (Task 15)
print("\n--- T78-T94: Career Panel static checks ---")
test("T78: index.html contains career-panel", 'id="career-panel"' in html)
test("T79: index.html career refresh button", 'id="career-refresh-btn"' in html)
test("T80: style.css career panel full width", ".career-panel" in css and "grid-column: 1 / -1" in css)
test("T81: career panel appears after growth panel", html.find('id="growth-panel"') < html.find('id="career-panel"'))
for label, ep in [
    ("T82: app.js GET /career/assets", "/career/assets"),
    ("T83: app.js GET /career/claims", "/career/claims"),
    ("T84: app.js GET /career/jds", "/career/jds"),
    ("T85: app.js GET /career/evaluations", "/career/evaluations"),
    ("T86: app.js GET /career/applications", "/career/applications"),
    ("T87: app.js GET /career/handoffs", "/career/handoffs"),
    ("T88: app.js POST /career/assets", "/career/assets"),
]:
    test(label, ep in js)
test("T89: app.js no direct career/ file access",
     "career/assets/" not in js and "career/claims/" not in js and "career/jds/" not in js and
     "career/evaluations/" not in js and "career/applications/" not in js and "career/handoffs/" not in js)
test("T90: app.js no career_center.py call", "career_center.py" not in js)
test("T91: app.js career create form ids", "career-asset-title" in js and "career-asset-type" in js and "career-evidence" in js)
test("T92: Career panel shows manual application state", "Auto Submit" in js)
test("T93: app.js no dangerous career patterns", "eval(" not in js_stripped and "new Function(" not in js_stripped and "child_process" not in js)
test("T94: refreshAll includes Career", "refreshCareer();" in js)

# Readiness Panels Tests (Tasks 16-20)
print("\n--- T95-T133: Readiness Panel static checks ---")
for pid in ["automation-panel", "skills-panel", "knowledge-panel", "model-panel", "mcp-panel"]:
    test("T95-panel-" + pid + ": exists", f'id="{pid}"' in html)
for cls in [".automation-panel", ".skills-panel", ".knowledge-panel", ".model-panel", ".mcp-panel"]:
    test("T96-style-" + cls + ": full width", cls in css and "grid-column: 1 / -1" in css)
for label, ep in [
    ("T97: GET /automation/workflows", "/automation/workflows"),
    ("T98: GET /automation/runs", "/automation/runs"),
    ("T99: GET /skills/candidates", "/skills/candidates"),
    ("T100: GET /skills/reviews", "/skills/reviews"),
    ("T101: GET /knowledge/nodes", "/knowledge/nodes"),
    ("T102: GET /knowledge/edges", "/knowledge/edges"),
    ("T103: GET /knowledge/boundaries", "/knowledge/boundaries"),
    ("T104: GET /knowledge/state", "/knowledge/state"),
    ("T105: GET /model/routes", "/model/routes"),
    ("T106: GET /model/cost-events", "/model/cost-events"),
    ("T107: GET /mcp/profiles", "/mcp/profiles"),
    ("T108: GET /mcp/tool-policies", "/mcp/tool-policies"),
    ("T109: POST /automation/workflows", "/automation/workflows"),
    ("T110: POST /skills/candidates", "/skills/candidates"),
    ("T111: POST /knowledge/nodes", "/knowledge/nodes"),
    ("T112: POST /model/routes", "/model/routes"),
    ("T113: POST /mcp/profiles", "/mcp/profiles"),
]:
    test(label, ep in js)
test("T114: no readiness script direct call", "readiness_center.py" not in js)
test("T115: no automation direct files", "automation/workflows/" not in js and "automation/runs/" not in js)
test("T116: no capability direct files", "capabilities/" not in js)
test("T117: no knowledge graph direct files", "knowledge_graph/" not in js)
test("T118: no model cost direct files", "model_cost/" not in js)
test("T119: no mcp direct files", "mcp/profiles/" not in js and "mcp/policies/" not in js)
test("T120: Automation shows disabled/preflight columns", "Enabled" in js and "Outputs" in js)
test("T121: Skills show sandbox/enabled columns", "Sandbox" in js and "Enabled After" in js)
test("T122: Knowledge shows RAG disabled state", "RAG" in js and "disabled" in js)
test("T123: Model panel shows LiteLLM", "LiteLLM" in js)
test("T124: MCP panel shows Write", "MCP Profiles" in js and "Write" in js)
test("T125: refreshAll includes Automation", "refreshAutomation();" in js)
test("T126: refreshAll includes Skills", "refreshSkills();" in js)
test("T127: refreshAll includes Knowledge", "refreshKnowledge();" in js)
test("T128: refreshAll includes Model/Cost", "refreshModelCost();" in js)
test("T129: refreshAll includes MCP", "refreshMcpTools();" in js)
test("T130: readiness create form ids", "automation-name" in js and "skill-name" in js and "knowledge-label" in js)
test("T131: model/mcp create form ids", "model-task-type" in js and "mcp-name" in js)
test("T132: no dangerous readiness patterns", "eval(" not in js_stripped and "new Function(" not in js_stripped and "child_process" not in js)
test("T133: mcp write disabled text", "write_actions_allowed" in js and "write_allowed" in js)

# Remote model provider and Chinese workbench checks
print("\n--- T134-T140: Remote model and Chinese workbench checks ---")
test("T134a: setup panel is the fifteenth panel", 'id="setup-panel"' in html and ".setup-panel" in css)
test("T134b: dashboard is Chinese", '<html lang="zh-CN">' in html and 'OnePal 本地工作台' in html)
test("T134c: provider form has required fields", all(token in html for token in [
    'id="provider-base-url"', 'id="provider-model"', 'id="provider-api-key"', 'id="provider-budget"',
]))
test("T134d: setup has provider API bindings", all(endpoint in js for endpoint in [
    "/model/provider", "/model/provider/test",
]))
test("T134e: assistant requires explicit remote confirmation", 'assistant-remote-confirm' in js and '本次内容将发送到远程模型服务' in js)
test("T134f: assistant posts only to proposal endpoint", "apiPost('/assistant/proposals'" in js)
test("T134g: setup page describes private local configuration", '本机私有目录' in html and '不会回显' in html)

# Dashboard UX Checks
print("\n--- T134-T142: Dashboard UX static checks ---")
test("T134: dashboard has panel navigation", 'class="panel-nav"' in html and 'class="nav-chip"' in html)
nav_targets = re.findall(r'class="nav-chip"\s+href="#([^"]+)"', html)
test("T135: panel navigation covers all panels", len(nav_targets) == 15 and all(f'id="{target}"' in html for target in nav_targets),
     f"nav_targets={nav_targets}")
test("T136: dashboard has toast live region", 'id="toast-region"' in html and 'aria-live="polite"' in html)
test("T137: app.js uses toast error handling", "function showToast" in js and "function handleActionError" in js)
test("T138: app.js has no blocking alert calls", "alert(" not in js_stripped)
test("T139: app.js dashboard panel count comment is current", "DOM rendering for 15 panels" in js)
test("T140: style.css supports smooth anchor navigation", "scroll-behavior: smooth" in css and "scroll-margin-top" in css)
test("T141: style.css has keyboard focus states", ":focus-visible" in css)
test("T142: style.css has mobile single-column layout", "@media (max-width: 900px)" in css and "grid-template-columns: 1fr" in css)

# Summary
print("\n" + "=" * 60)
total = passed + failed
print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
