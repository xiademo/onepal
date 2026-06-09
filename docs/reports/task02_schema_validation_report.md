# Task 02 Schema Validation Report

Generated: 2026-06-09 10:35:29 +08

## 1. Summary

  [PASS] schemas/registry.json exists
  [PASS] schemas/core/ directory exists

## 2. Registry Completeness

  [PASS] schemas/registry.json parsed (version: 1.4.0)
  Registry: 41 entries   Core files: 41

  ### Registry -> File
  [PASS] All 41 registry entries resolve to existing files

  ### File -> Registry
  [PASS] All 41 core schemas are registered

  ### Metadata
  [PASS] Metadata scan complete

## 3. $ref Reference Check

  [PASS] $ref check: 0 references across 41 schemas, 0 broken

## 4. Core Schema Compile (ajv --spec=draft2019)

    [PASS] action_execution.schema.json
    [PASS] action.schema.json
    [PASS] agent.schema.json
    [PASS] application_record.schema.json
    [PASS] approval_decision.schema.json
    [PASS] boundary_candidate.schema.json
    [PASS] builder_task_prompt.schema.json
    [PASS] career_asset.schema.json
    [PASS] cost_event.schema.json
    [PASS] document_packet.schema.json
    [PASS] evidence_pack.schema.json
    [PASS] handoff.schema.json
    [PASS] jd_evaluation.schema.json
    [PASS] jd_item.schema.json
    [PASS] knowledge_edge.schema.json
    [PASS] knowledge_node.schema.json
    [PASS] knowledge_state.schema.json
    [PASS] mcp_server_profile.schema.json
    [PASS] memory_candidate.schema.json
    [PASS] memory_change_request.schema.json
    [PASS] memory_conflict.schema.json
    [PASS] memory_entry.schema.json
    [PASS] memory_quality_review.schema.json
    [PASS] memory_snapshot.schema.json
    [PASS] model_router.schema.json
    [PASS] permission_profile.schema.json
    [PASS] proposal.schema.json
    [PASS] research_packet.schema.json
    [PASS] resume_claim.schema.json
    [PASS] runtime_service.schema.json
    [PASS] skill.schema.json
    [PASS] smoke_test.schema.json
    [PASS] source_evaluation.schema.json
    [PASS] state_transition.schema.json
    [PASS] subtask_request.schema.json
    [PASS] task_tree.schema.json
    [PASS] task.schema.json
    [PASS] tool_adapter.schema.json
    [PASS] tool_trust_policy.schema.json
    [PASS] workflow_run.schema.json
    [PASS] workflow.schema.json
  [PASS] All 41 core schemas compile successfully

## 5. Example Validation

  [PASS] action.example.json validates ok
  [PASS] permission_profile.example.json validates ok
  [PASS] approval_decision.example.json validates ok
  [PASS] task.example.json validates ok
  [PASS] task_tree.example.json validates ok
  [PASS] runtime_service.example.json validates ok
  Result: 6 passed, 0 failed

## 6. BOM Cleanup & Stub Normalization

  [PASS] BOM removed: memory\preferences.json
  [PASS] BOM removed: memory\decisions.json
  [PASS] BOM removed: agents\registry.json
  [PASS] stub ok: workflows\features.json
  [PASS] stub ok: workflows\approvals.json
  [PASS] stub ok: skills\index.json

## 7. Overall Results

| Category | PASS | WARN | FAIL |
|----------|------|------|------|
| Total    | 20 | 0 | 0 |

## 8. Next Step

All checks passed. Registry complete, schemas compile, examples validate.
Ready for Task 02-B or Task 03.
