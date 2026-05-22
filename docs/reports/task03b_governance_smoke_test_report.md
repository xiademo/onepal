# Task 03-B Governance Smoke Test Report

Generated: 2026-05-22T13:15:21.177856+00:00

## 1. Summary

| Phase | Status |
|-------|--------|
| Governance Tests (T1-T12) | PASS |
| Schema Validation | PASS |
| JSONL Parse Audit | PASS |
| Git Check-Ignore | PASS |
| **Overall** | **PASS** |

## 2. Governance Tests (T1-T12)

```
============================================================
OnePal Governance Loop Tests
============================================================

--- T1: Unregistered action rejected ---
  [PASS] T1: unregistered action rejected

--- T2: safe_readonly dry-run read_file ---
  [PASS] T2: safe_readonly dry-run

--- T3: R0 read_file without approval ---
  [PASS] T3: R0 action without approval

--- T4: R2 action without approval rejected ---
  [PASS] T4: R2 action without approval rejected

--- T5: safe_readonly cannot approve ---
  [PASS] T5: safe_readonly cannot approve

--- T6: create_proposal dry-run ---
  [PASS] T6: create_proposal dry-run

--- T7: rejected proposal blocked ---
  [PASS] T7: rejected proposal blocked

--- T8: state_mutation writes audit ---
  [PASS] T8: state_mutation writes audit

--- T9: action_executions.jsonl has records ---
  [PASS] T9: execution records exist

--- T10: all runtime JSONL parseable ---
  [PASS] T10: JSONL parseable

--- T11: disabled action rejected (G2) ---
  [PASS] T11: disabled action rejected (G2)

--- T12: expired approval rejected (G5) ---
  [PASS] T12: expired approval rejected (G5)

============================================================
Results: 12/12 PASS, 0/12 FAIL
============================================================

```

## 3. Schema Validation

```
rkspaces\onepal
  PASS: schemas/registry.json exists
  PASS: schemas/core/ directory exists
  PASS: schemas/registry.json parsed (version: 1.1.0)
  PASS: All 22 registry entries resolve to existing files
  PASS: All 22 core schemas are registered
  PASS: Metadata scan complete
  PASS: $ref check: 0 references across 22 schemas, 0 broken
  PASS: All 22 core schemas compile successfully
  PASS: action.example.json validates ok
  PASS: permission_profile.example.json validates ok
  PASS: approval_decision.example.json validates ok
  PASS: task.example.json validates ok
  PASS: task_tree.example.json validates ok
  PASS: runtime_service.example.json validates ok
  PASS: BOM removed: memory\preferences.json
  PASS: BOM removed: memory\decisions.json
  PASS: BOM removed: agents\registry.json
  PASS: stub ok: workflows\features.json
  PASS: stub ok: workflows\approvals.json
  PASS: stub ok: skills\index.json

Report: D:\git\ai\workspaces\onepal\docs\reports\task02_schema_validation_report.md

```

## 4. JSONL Parse Audit

Total JSONL lines: 2, bad: 0

## 5. Git Check-Ignore

```
  [IGNORED] runtime/actions/action_executions.jsonl -> .gitignore:16:runtime/**/*.jsonl	runtime/actions/action_executions.jsonl
  [IGNORED] runtime/audit/state_mutation_audit.jsonl -> .gitignore:16:runtime/**/*.jsonl	runtime/audit/state_mutation_audit.jsonl
  [IGNORED] runtime/approvals/proposals.jsonl -> .gitignore:16:runtime/**/*.jsonl	runtime/approvals/proposals.jsonl
  [IGNORED] runtime/approvals/approval_decisions.jsonl -> .gitignore:16:runtime/**/*.jsonl	runtime/approvals/approval_decisions.jsonl
```

## 6. Warnings

None.

## 7. Failures

0

## 8. Next Step Recommendation

All governance smoke tests passed. Ready for Task 04.
