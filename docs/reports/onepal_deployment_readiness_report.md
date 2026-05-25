# OnePal Deployment Readiness Report

Generated: 2026-05-25T01:45:00Z
Audit Type: Full Functional Verification + Deployment Readiness
Scope: Task 01.5 through Task 05-B

---

## 1. Executive Summary

### Verdict: **READY_FOR_TASK_06**

**Reason**: All 49 tests across 6 test suites pass. Schema validation, governance loop, command gateway, runtime runner, startup smoke test, and governance smoke test all operational. No runtime JSONL leaks. No secrets detected. Environment fully inventoried. Core P0 capabilities complete and verified.

---

## 2. Project Progress

| Task | Status | Core Artifacts | Tests | Committed | Notes |
|------|--------|---------------|-------|-----------|-------|
| 01.5 | ✅ Complete | Project scan report | — | — | Read-only audit |
| 02-A | ✅ Complete | 22 schemas hardened, validation script | Schema 22/22 compile | 5af99cd | BOM removed, ajv validated |
| 03-A | ✅ Complete | Action Registry, Permission Profiles, 3 governance scripts | 12/12 T1-T12 PASS | a5c498c | 7-guard pipeline |
| 03-B | ✅ Complete | Governance smoke test automation | 12/12 PASS + smoke runner | 72e3cf2 | Runtime test isolation |
| 04-A | ✅ Complete | Runtime Service Registry, Startup Smoke Test | 10/10 T1-T10 PASS | 13ac7b3 | Health=ready |
| 05-A | ✅ Complete | Command Gateway, Task Tree, Routing | 12/12 T1-T12 PASS | 0d9019f | Deterministic routing |
| 05-B | ✅ Complete | Runtime Runner, Allowlist, Execution Bridge | 15/15 T1-T15 PASS | **NOT COMMITTED** | Awaiting user commit |
| 06 | ⬚ Pending | Minimum API Server | — | — | Next step |
| 07 | ⬚ Pending | Dashboard Workbench | — | — | After Task 06 |
| 08+ | ⬚ Pending | Memory Center, Research, etc. | — | — | Future |

---

## 3. Implemented Capability Inventory

### Schema Registry
- `schemas/registry.json` (v1.1.0): 22 registered core schemas
- `schemas/core/*.schema.json`: action, action_execution, agent, approval_decision, document_packet, evidence_pack, handoff, memory_candidate, permission_profile, proposal, research_packet, runtime_service, skill, smoke_test, source_evaluation, state_transition, subtask_request, task, task_tree, tool_adapter, workflow, workflow_run
- `scripts/validate_schema_registry.ps1`: ajv compile + `$ref` check + registry/file cross-reference
- **Status**: ✅ Complete, 22/22 compile, 0 broken `$ref`

### Governance
- `registries/action_registry.json`: 5 actions (read_file, create_proposal, approve_proposal, reject_proposal, archive_proposal)
- `policies/permission_profiles.json`: 2 profiles (safe_readonly, local_write_with_approval)
- `scripts/check_permission.py`: action + profile authorization check
- `scripts/request_action.py`: 7-guard action execution pipeline (G1 action registered, G2 enabled, G3 profile authorized, G4 approval required, G5 not expired, G6 proposal state check, G7 audit for state_mutation)
- `scripts/decide_proposal.py`: human approval entry point + test fixtures
- `tests/test_governance_loop.py`: 12 automated governance tests
- `scripts/run_governance_smoke_test.py`: governance smoke test runner
- **Status**: ✅ Complete, 12/12 T1-T12 PASS

### Runtime Health
- `registries/runtime_service_registry.json`: 4 registered services
- `scripts/run_startup_smoke_test.py`: 9-check health scanner (services, files, schema, governance, writes, gitignore, secrets, lock, write mode)
- `scripts/check_runtime_lock.py`: system lock checker
- `scripts/check_write_mode.py`: write mode checker (local_dry_run, local_write_with_approval, safe_readonly, locked)
- `tests/test_startup_smoke_test.py`: 10 automated tests
- `runtime/README.md`: runtime directory policy
- `logs/README.md`: logs directory policy
- **Status**: ✅ Complete, Health=ready after clean runtime state

### Command Gateway
- `workflows/coordinator_routes.json` (v0.2): 5 deterministic command routes + agent routes
- `scripts/command_gateway.py`: receives commands, routes deterministically, creates task trees, writes MAS trace
- `tests/test_command_gateway.py`: 12 automated tests
- **Status**: ✅ Complete, 12/12 T1-T12 PASS

### Task Tree
- `scripts/task_tree.py`: CRUD operations for tasks and task_trees (create, add child, update status, read)
- Uses task.schema.json and task_tree.schema.json compliant status values
- **Status**: ✅ Complete, tested via T8 in command_gateway tests

### Runtime Runner
- `scripts/runtime_runner.py`: controlled execution bridge with subprocess isolation
- `workflows/runtime_execution_allowlist.json`: script and action allowlist configuration
- `schemas/examples/task_run.example.json`: future schema draft
- `tests/test_runtime_runner.py`: 15 automated tests
- **Status**: ✅ Complete, 15/15 T1-T15 PASS (NOT COMMITTED)

### MAS Trace
- `logs/mas_trace.jsonl`: full pipeline trace (command_received → routed → task_tree_created → runner_executing → runner_completed/failed)
- Written by command_gateway.py and runtime_runner.py
- **Status**: ✅ Complete, gitignored

### Gitignore / Runtime Data Isolation
- `.gitignore`: 49 lines covering node_modules, OpenCode state, runtime JSONL (all nested paths), runtime config files, health_status, runtime_lock, write_mode, logs JSONL, secrets, credentials
- **Status**: ✅ Verified — all runtime/logs JSONL properly excluded

---

## 4. Verification Result

| Test Suite | PASS | FAIL | Status |
|-----------|------|------|--------|
| `test_governance_loop.py` | 12 | 0 | ✅ PASS |
| `test_startup_smoke_test.py` | 10 | 0 | ✅ PASS |
| `test_command_gateway.py` | 12 | 0 | ✅ PASS |
| `test_runtime_runner.py` | 15 | 0 | ✅ PASS |
| `run_startup_smoke_test.py` | — | — | ✅ Health: ready |
| `run_governance_smoke_test.py` | — | — | ✅ Overall: PASS |
| `validate_schema_registry.ps1` | 20 | 0 | ✅ 22/22 compile |

**Total: 49 unit tests + 3 system tests — all PASS, 0 FAIL**

---

## 5. Code Quality / CodeSimplify Review

### Complexity Assessment: **LOW complexity**

| Metric | Rating | Notes |
|--------|--------|-------|
| Lines per script | < 360 lines | All scripts are concise, single-file |
| Function size | < 40 lines | Most functions are 5-20 lines |
| Nesting depth | ≤ 3 levels | Shallow, readable |
| Magic strings | Few | Mostly CLI args and file paths |

### Readability: **GOOD**

- Consistent JSONL append/write/load patterns across all scripts
- All scripts use `argparse` with clear `--help`
- Docstrings at module and function level
- ISO 8601 timestamps throughout
- UUID-based IDs with meaningful prefixes (cmd_, task_, tree_, route_, etc.)

### Duplicate Logic: **MINIMAL**

- `load_jsonl()` and `append_jsonl()` duplicated across 4 scripts — acceptable given single-file constraint and no shared library
- `now_iso()` duplicated across 4 scripts — same rationale
- **Recommendation**: Future task could extract shared utilities into `scripts/lib/utils.py`

### Test Quality: **GOOD**

- All tests use `tempfile.TemporaryDirectory()` for isolation
- T9 regression was identified and fixed (flaky due to shared temp dir)
- T1-T15 cover allowlist enforcement, status transitions, MAS trace, gitignore, and regression
- Test fixtures use manually created task dicts rather than gateway output for deterministic testing

### Maintainability: **GOOD**

- All paths support CLI override (`--tasks-log`, `--task-runs-log`, etc.) enabling test isolation
- Clear separation: Gateway (scheduling) → Runner (execution) → request_action (governance)
- Allowlist is external JSON config, not hardcoded

### No Blocking Issues

---

## 6. Security and Governance Review

| Check | Result | Evidence |
|-------|--------|----------|
| `shell=True` in scripts | ✅ 0 hits | rg audit confirms no `shell=True`, `os.system`, `popen`, `eval()`, `exec()` |
| Allowlist enforcement | ✅ Active | Runner checks `allowed_scripts` and `allowed_actions` before execution |
| action_ref delegation | ✅ Enforced | Runner delegates to `request_action.py` via subprocess; never bypasses 7-guard |
| R2+ approval gate | ✅ Enforced | `action.approve_proposal` not in allowlist; G4 guard rejects R2 without approval |
| Forbidden extensions | ✅ Enforced | `.ps1/.bat/.exe/.sh/.cmd/.vbs` rejected by allowlist check |
| Path traversal | ✅ Enforced | `../` in `forbidden_paths`; runner rejects absolute or relative-traversal paths |
| Secret scan | ✅ 0 hits | rg audit excludes docs/md/scanner files — 0 genuine secrets |
| runtime JSONL gitignore | ✅ All covered | git check-ignore confirms all 7 runtime/logs paths |
| Write to approval_decision | ✅ Not performed | Runner never writes approval decisions |
| Direct memory write | ✅ Not performed | Runner never writes to memory/ |

---

## 7. Environment Inventory

| Attribute | Value |
|-----------|-------|
| **OS** | Windows (win32) |
| **Shell** | PowerShell 5.1 |
| **Python** | 3.11.8 (via `py` launcher, `C:\Windows\py.exe`) |
| **Node** | v22.14.0 (`C:\Program Files\nodejs\node.exe`) |
| **pnpm** | ❌ Not available |
| **Git** | 2.54.0.windows.1 |
| **rg (ripgrep)** | 15.1.0 (WinGet) |
| **gh (GitHub CLI)** | 2.92.0 (2026-04-28) |
| **ajv-cli** | Available (npm-global, `--spec=draft2019`) |
| **OpenCode** | 1.14.32 |
| **OmO** | ❌ Not available as CLI |
| **MCP** | 0 (disabled) |
| **LSP** | 0 (disabled) |
| **Docker / services** | 0 (disabled, not running) |
| **Working directory** | `D:\git\ai\workspaces\onepal` |
| **Git branch** | `master` |
| **Latest commit** | `0d9019f` — feat(command): add gateway routing and task tree baseline |
| **Uncommitted changes** | Task 05-B files (6 modified, 4 new) |

---

## 8. Deployment Plan

### 8.1 Current: Local Dev Runtime Deployment

**Status**: ✅ Operational

**How to deploy on a new machine**:
```bash
git clone <repo> D:\git\ai\workspaces\onepal
cd D:\git\ai\workspaces\onepal

# Verify environment
py --version          # must be 3.11+
rg --version           # must be available
ajv --version          # must be available

# Run all tests
py tests\test_governance_loop.py
py tests\test_startup_smoke_test.py
py tests\test_command_gateway.py
py tests\test_runtime_runner.py

# Run smoke tests
py scripts\run_startup_smoke_test.py
py scripts\run_governance_smoke_test.py

# Schema validation
powershell -ExecutionPolicy Bypass -File scripts\validate_schema_registry.ps1

# Verify git hygiene
git status --short    # should show no runtime/**/*.jsonl or logs/**/*.jsonl
```

### 8.2 Next: Task 06 — Local API Control Plane

**Goal**: Add a minimal HTTP API server (Python stdlib `http.server` + `json`) that:
- Provides read-only access to health, task tree, runner executions, and MAS trace
- Does NOT: execute actions, bypass governance, write to runtime, expose secrets, accept untrusted input

**Minimum endpoints** (PLAN ONLY, do not implement yet):
```
GET  /health           → runtime/health_status.json
GET  /tasks            → runtime/tasks/tasks.jsonl (latest N)
GET  /task-trees       → runtime/tasks/task_trees.jsonl
GET  /task-runs        → runtime/task_runs/task_runs.jsonl (latest N)
GET  /mas-trace        → logs/mas_trace.jsonl (latest N)
POST /command          → proxy to command_gateway.py (with allowlist check)
```

**Constraints**:
- API must NOT bypass governance
- API must NOT execute R2+ actions
- API must NOT write to runtime directly
- API must bind to `127.0.0.1` only
- All responses JSON, no HTML rendering

### 8.3 Future: Task 07+ — Local Dashboard Workbench

**Goal**: HTML/CSS/JS dashboard that:
- Calls the API Server (Task 06) for data
- Displays: Health, Command History, Task Tree, Task Runs, MAS Trace, Audit
- Does NOT: bypass gateway, runner, or governance
- Runs entirely local, no external CDN

---

## 9. Risks and Open Issues

| Risk | Severity | Mitigation |
|------|----------|------------|
| Task 05-B not committed | Low | Manual commit needed before Task 06; no data loss risk |
| Trailing whitespace in .gitignore (lines 25-26) | Low | Cosmetic; `git diff --check` flags it but doesn't block |
| Smoke test reports auto-refresh on run | Low | Expected behavior; old reports may show stale timestamps |
| `python` not in PATH (only `py` launcher) | Medium | All scripts use `py` command; document this in deployment guide |
| pnpm not available | Low | Not currently needed; install if Node.js tooling required |
| No shared utility library | Low | `load_jsonl`/`now_iso`/`append_jsonl` duplicated; extract in future task |
| Runtime state stale after test runs | Low | Clean with `Remove-Item runtime\*\* -Force` before smoke tests |

---

## 10. Final Recommendation

### ✅ **READY_FOR_TASK_06**

**All verification gates pass**:
- 49/49 unit tests + 3/3 system tests = 0 FAIL
- 25/25 core files exist
- 0 secrets detected
- 0 shell=True or dangerous execution
- Allowlist enforcement active
- Governance loop intact (Gateway → Runner → request_action)
- runtime/logs fully gitignored

**Before entering Task 06**, user should:
1. Commit Task 05-B changes:
   ```
   git add .gitignore runtime/README.md scripts/command_gateway.py scripts/runtime_runner.py tests/test_runtime_runner.py workflows/runtime_execution_allowlist.json schemas/examples/task_run.example.json docs/reports/
   git commit -m "feat(runtime): add controlled execution bridge with allowlist"
   ```
2. Verify `git status --short` is clean after commit

**Suggested commit message**: `feat(runtime): add controlled execution bridge with allowlist`
