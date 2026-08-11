#!/usr/bin/env python3
"""OnePal Task 14-A schema pack tests.

These tests avoid external JSON Schema dependencies. They validate the schema
pack contract with the JSON Schema subset used by the imported builder/memory
schemas: required fields, types, enum, const, pattern, min/max, arrays, object
properties, additionalProperties, and simple if/then rules.

Usage: py tests/test_schema_pack_builder_memory.py
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "schemas" / "core"
REGISTRY = PROJECT_ROOT / "schemas" / "registry.json"

TARGET_SCHEMA_IDS = [
    "builder_task_prompt.schema.json",
    "memory_entry.schema.json",
    "memory_conflict.schema.json",
    "memory_quality_review.schema.json",
    "memory_change_request.schema.json",
    "memory_snapshot.schema.json",
]

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
            print(f"         {msg}")
    return ok


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_type(value, expected):
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate(value, schema, path="$"):
    errors = []
    expected_type = schema.get("type")
    if expected_type:
        expected = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(is_type(value, t) for t in expected):
            return [f"{path}: expected {expected_type}, got {type(value).__name__}"]

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum")
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: value {value!r} does not match const")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: does not match pattern {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems")
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(value):
                errors.extend(validate(item, item_schema, f"{path}[{idx}]"))
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required {key}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(props))
            if extra:
                errors.append(f"{path}: additional properties {extra}")
        for key, child_schema in props.items():
            if key in value:
                errors.extend(validate(value[key], child_schema, f"{path}.{key}"))
    for clause in schema.get("allOf", []):
        condition = clause.get("if")
        then_schema = clause.get("then")
        if condition and then_schema and not validate(value, condition, path):
            errors.extend(validate(value, then_schema, path))
    return errors


def score_block(value=0.9):
    return {
        "clarity": value,
        "specificity": value,
        "evidence_strength": value,
        "stability": value,
        "actionability": value,
        "non_sensitivity": value,
        "non_duplicate": value,
        "scope_fit": value,
    }


def valid_builder_prompt():
    return {
        "builder_task_prompt_id": "btp_task14_a",
        "task_id": "task_14_a",
        "title": "Schema pack integration",
        "task_stage": "build",
        "opencode_mode": "Build",
        "omo_agent": "Hephaestus",
        "model": {"provider": "local", "name": "codex", "tier": "local"},
        "thinking_intensity": "medium",
        "task_objective": "Add schema pack contracts without runtime behavior changes.",
        "project_context": {
            "project_name": "OnePal",
            "repo_path": "D:/git/ai/workspaces/onepal",
            "branch_policy": "current_branch_only",
            "baseline_doc_refs": ["docs/reports/task13_growth_api_dashboard_report.md"],
        },
        "permissions": {
            "file_write": {
                "allowed": True,
                "allowed_paths": ["schemas/core", "schemas/registry.json", "tests"],
                "forbidden_paths": ["OpenCode", "memory/store.json"],
                "requires_diff_summary": True,
            },
            "dependency_install": {
                "allowed": False,
                "approval_required": True,
                "allowed_package_managers": [],
            },
            "network": {"allowed": False, "approval_required": True, "allowed_domains": []},
            "mcp_lsp_service": {
                "mcp_allowed": False,
                "lsp_allowed": False,
                "service_start_allowed": False,
                "approval_required": True,
                "allowed_ports": [],
            },
            "runtime_service": {
                "can_start": False,
                "can_stop": False,
                "can_modify_registry": False,
                "approval_required": True,
            },
            "memory_write": {"mode": "direct_store_forbidden", "approval_required": True},
            "secrets_access": "forbidden",
        },
        "safety_constraints": {
            "no_shell_true": True,
            "no_secrets": True,
            "no_unapproved_mcp": True,
            "no_runtime_jsonl_git": True,
            "no_direct_memory_store": True,
            "no_unrelated_refactor": True,
            "no_external_script_exec": True,
            "action_registry_required": True,
            "permission_check_required": True,
        },
        "allowed_scope": ["schemas", "tests", "docs"],
        "forbidden_scope": ["OpenCode", "secrets", "runtime data"],
        "expected_outputs": [
            {"output_type": "schema", "path_or_ref": "schemas/core", "description": "schema files"}
        ],
        "acceptance_tests": [
            {
                "test_id": "test_schema_pack",
                "test_type": "pytest",
                "command": "py -m pytest tests/test_schema_pack_builder_memory.py",
                "description": "schema pack tests pass",
                "expected_result": "0 failures",
                "required": True,
            }
        ],
        "rollback_plan": {"required": True, "strategy": "revert schema pack commit"},
        "report_path": "docs/reports/task14_final_goal_foundation_report.md",
        "status": "issued",
        "created_at": "2026-06-08T00:00:00Z",
        "updated_at": None,
    }


def valid_memory_entry():
    return {
        "memory_id": "mem_task14_a",
        "source_candidate_ref": "memcand_task14_a",
        "memory_type": "project_state",
        "content": "Task 13-B Growth API Dashboard is complete.",
        "structured_data": None,
        "summary": "Growth API Dashboard baseline.",
        "scope": {"visibility": "project", "project_id": "onepal", "applies_to": ["OnePal"]},
        "status": "active",
        "sensitivity": "internal",
        "confidence": 0.9,
        "retention_policy": {
            "class": "long",
            "review_after_days": 180,
            "decay_policy": "review_before_reuse",
        },
        "provenance": {
            "origin_type": "user_confirmed",
            "source_refs": ["docs/reports/task13_growth_api_dashboard_report.md"],
            "created_by_agent": "Memory Curator",
        },
        "quality": {
            "quality_review_ref": "memqr_task14_a",
            "overall_score": 0.9,
            "last_reviewed_at": "2026-06-08T00:00:00Z",
        },
        "approval_ref": "approval_task14_a",
        "conflict_refs": [],
        "supersedes_refs": [],
        "superseded_by_ref": None,
        "version": 1,
        "created_at": "2026-06-08T00:00:00Z",
        "updated_at": "2026-06-08T00:00:00Z",
    }


def examples():
    return {
        "builder_task_prompt.schema.json": valid_builder_prompt(),
        "memory_entry.schema.json": valid_memory_entry(),
        "memory_conflict.schema.json": {
            "memory_conflict_id": "memconf_task14_a",
            "conflict_type": "duplicate",
            "severity": "low",
            "status": "open",
            "summary": "Candidate duplicates existing project state.",
            "detected_at": "2026-06-08T00:00:00Z",
            "detected_by": "Memory Curator",
            "candidate_ref": "memcand_task14_a",
            "existing_memory_refs": ["mem_existing_a"],
            "recommended_resolution": "merge",
            "resolution": {"strategy": "unresolved", "requires_user_approval": True},
        },
        "memory_quality_review.schema.json": {
            "memory_quality_review_id": "memqr_task14_a",
            "target_type": "candidate",
            "target_ref": "memcand_task14_a",
            "reviewer_agent": "Memory Curator",
            "created_at": "2026-06-08T00:00:00Z",
            "scores": score_block(),
            "overall_score": 0.9,
            "issues": [],
            "recommendation": "approve",
            "requires_user_confirmation": False,
            "suggested_scope": "project",
            "suggested_retention": "long",
            "review_notes": "Specific and stable.",
        },
        "memory_change_request.schema.json": {
            "memory_change_request_id": "memchg_task14_a",
            "change_type": "create",
            "requested_by": "Memory Curator",
            "risk_level": "R3",
            "requires_user_approval": True,
            "status": "pending_review",
            "reason": "Create reviewed memory entry.",
            "target_refs": ["memcand_task14_a", "memqr_task14_a"],
            "proposed_entry": valid_memory_entry(),
            "merge_sources": [],
            "approval_ref": None,
            "rollback_plan": {"available": True, "strategy": "restore snapshot", "snapshot_ref": "memsnap_task14_a"},
            "created_at": "2026-06-08T00:00:00Z",
            "updated_at": None,
        },
        "memory_snapshot.schema.json": {
            "memory_snapshot_id": "memsnap_task14_a",
            "created_at": "2026-06-08T00:00:00Z",
            "created_by": "Memory Curator",
            "reason": "Before memory change request execution.",
            "storage_path": "memory/snapshots/memsnap_task14_a.json",
            "content_hash": None,
            "included_scopes": ["project"],
            "entry_count": 1,
            "status": "created",
            "restore_available": True,
            "notes": "metadata only in test",
        },
    }


def run_valid_examples():
    print("\n--- T4: valid examples satisfy imported schemas ---")
    ok = True
    for sid, data in examples().items():
        schema = load_json(SCHEMA_DIR / sid)
        errors = validate(data, schema)
        ok = test(f"T4-{sid}: valid example accepted", not errors, "; ".join(errors[:3])) and ok
    return ok


def run_invalid_examples():
    print("\n--- T5: invalid examples rejected ---")
    checks = []
    quality = examples()["memory_quality_review.schema.json"]
    quality_missing = dict(quality)
    quality_missing.pop("target_ref")
    checks.append(("missing required target_ref", "memory_quality_review.schema.json", quality_missing))

    change = examples()["memory_change_request.schema.json"]
    bad_change = dict(change)
    bad_change["change_type"] = "direct_store"
    checks.append(("invalid change_type enum", "memory_change_request.schema.json", bad_change))

    conflict = examples()["memory_conflict.schema.json"]
    bad_conflict = dict(conflict)
    bad_conflict["existing_memory_refs"] = ["candidate_without_mem_prefix"]
    checks.append(("invalid memory ref pattern", "memory_conflict.schema.json", bad_conflict))

    builder = examples()["builder_task_prompt.schema.json"]
    bad_builder = json.loads(json.dumps(builder))
    bad_builder["safety_constraints"]["no_direct_memory_store"] = False
    checks.append(("builder safety const enforced", "builder_task_prompt.schema.json", bad_builder))

    ok = True
    for label, sid, data in checks:
        errors = validate(data, load_json(SCHEMA_DIR / sid))
        ok = test(f"T5: {label}", bool(errors), "invalid data unexpectedly passed") and ok
    return ok


def version_at_least(value, minimum):
    def parts(v):
        return [int(p) for p in str(v).split(".")[:3]]
    return parts(value) >= parts(minimum)


def main():
    print("=" * 60)
    print("OnePal Schema Pack Builder/Memory Tests")
    print("=" * 60)

    print("\n--- T1: schema files exist and parse ---")
    for sid in TARGET_SCHEMA_IDS:
        path = SCHEMA_DIR / sid
        ok = path.exists()
        if ok:
            try:
                schema = load_json(path)
                ok = bool(schema.get("$schema") and schema.get("$id") and schema.get("title"))
            except json.JSONDecodeError:
                ok = False
        test(f"T1-{sid}: exists and has metadata", ok)

    print("\n--- T2: registry includes schema pack ---")
    registry = load_json(REGISTRY)
    entries = {entry["schema_id"]: entry for entry in registry.get("schemas", [])}
    test("T2: registry version advanced", version_at_least(registry.get("version"), "1.2.0"), registry.get("version"))
    for sid in TARGET_SCHEMA_IDS:
        entry = entries.get(sid)
        ok = bool(entry and entry.get("status") == "active" and entry.get("path") == f"schemas/core/{sid}")
        test(f"T2-{sid}: registered active", ok, str(entry))

    print("\n--- T3: Memory Curator owns memory governance schemas ---")
    memory_ids = [sid for sid in TARGET_SCHEMA_IDS if sid.startswith("memory_")]
    for sid in memory_ids:
        test(f"T3-{sid}: owner Memory Curator", entries[sid]["owner"] == "Memory Curator")

    run_valid_examples()
    run_invalid_examples()

    print("\n" + "=" * 60)
    total = passed + failed
    print(f"Results: {passed}/{total} PASS, {failed}/{total} FAIL")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
