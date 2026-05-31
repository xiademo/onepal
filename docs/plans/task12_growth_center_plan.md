# OnePal Task 12 Growth Center Plan

Status: PLAN_READY_FOR_TASK_12B_BUILD | Generated: 2026-05-26

---

## 1. Purpose

Design OnePal's Growth Center: goal intake → contract → capacity planning → weekly/daily execution → review → adjustment. Converts research handoffs, user input, and cognition insights into executable growth plans.

## 2. Scope (P0)

- Goal candidate intake (manual + research_handoff + cognition_card)
- Goal contract creation (why, success criteria, minimum viable result)
- Capacity budget (time/energy/resource constraints)
- Weekly plans with goal-to-task decomposition
- Daily task tracking (planned/doing/done/skipped/blocked)
- Growth review with evidence, blockers, lessons learned
- Plan adjustment proposals (pause/resume/reduce/increase/change)
- Memory handoff candidates (no direct write)
- Research handoff consumption
- Growth audit logging
- Growth JSONL gitignore

## 3. Non-Goals

❌ API/Dashboard integration (Task 13+)
❌ Calendar/n8n automation
❌ Auto-time tracking
❌ Career Center integration
❌ Core schema modifications (goal_contract/growth_review schemas don't exist)

## 4. Source of Truth Boundary

| Domain | Source of Truth | Growth Center Role |
|--------|----------------|-------------------|
| Growth | growth/**/*.jsonl | **Primary** |
| Memory | memory/store/*.jsonl | Receives handoff candidates only |
| Research | research/**/*.jsonl | Consumes growth_handoffs |
| Career | Future Career Center | Produces career_handoffs; receives career gap input |

## 5. Growth Lifecycle

```
goal candidate → accept/reject → goal contract → capacity budget
  → weekly plan → daily tasks → do/skip/block → growth review
    → adjustment proposal → memory candidate (optional)
```

## 6. Goal Candidate Design

| Field | Type | Notes |
|-------|------|-------|
| candidate_id | pattern: `gocand_*` | Auto-generated |
| source_type | enum | manual, research_handoff, cognition_card, career_gap, memory_suggestion, review_feedback |
| source_id | string | Link to source (research handoff, card, etc.) |
| title | string | Required |
| goal_area | enum | ai_engineering, career, research, communication, health, finance, productivity, personal_project, other |
| reason | string | Why this goal |
| expected_outcome | string | |
| time_horizon | enum | 1w, 2w, 1m, 3m, 6m, 1y |
| priority_hint | P0-P3 | |
| confidence | 0.0-1.0 | < 0.5 → review required |
| status | captured/reviewed/accepted/rejected/converted_to_goal/archived | |

## 7. Goal Contract Design (dict-based, no schema)

| Field | Type | Notes |
|-------|------|-------|
| goal_id | pattern: `goal_*` | Auto-generated |
| title | string | |
| goal_area | enum | Same as candidate |
| why_it_matters | string | Required |
| desired_outcome | string | |
| success_criteria | string[] | At least 1 required |
| minimum_viable_result | string | Required |
| stretch_result | string | Optional |
| start_date | ISO8601 | |
| target_date | ISO8601 | |
| priority | P0-P3 | |
| status | draft/active/paused/completed/cancelled/archived | |
| source_candidate_id | string | Link back |

## 8. Capacity Budget Design

| Field | Type | Notes |
|-------|------|-------|
| budget_id | pattern: `cap_*` | |
| period_type | daily/weekly/monthly | |
| period_start/end | ISO8601 | |
| available_hours | float | |
| focus_slots | int | |
| energy_level | low/medium/high | |
| active_goal_ids | string[] | |
| reserved_hours_by_goal | dict | |
| overload_warning | boolean | Auto-computed |

## 9. Weekly Plan / Daily Task Design

**Weekly Plan**: week_start, week_end, goal_ids, focus_theme, planned_tasks, expected_outputs, risk_notes, status.

**Daily Task**: task_id, date, goal_id, title, description, estimated_minutes, task_type (study/build/review/write/practice/research/job_search/maintenance/other), status (planned/doing/done/skipped/blocked/cancelled).

## 10. Growth Review Design

review_id, period_type, period_start/end, goal_id, completed_tasks, missed_tasks, evidence_summary, self_rating (1-5), blockers, lessons_learned, adjustment_needed (boolean), memory_candidate_suggestion (optional text), created_at.

## 11. Plan Adjustment Proposal

proposal_id, proposal_type (growth_plan_adjustment), goal_id, reason, current_state_summary, proposed_change, impact (low/medium/high), risk_level (R0-R3), approval_required (boolean), status.

Change types: pause/resume/reduce_scope/increase_scope/change_deadline/change_priority/archive_goal/split/merge/adjust_capacity.

## 12. Handoff Boundary

| Source → Target | Mechanism | Constraint |
|-----------------|-----------|------------|
| Research → Growth | Read research/handoffs/growth_handoffs.jsonl | Low confidence → not P0 |
| Cognition Card → Growth | Manual trigger | Card topic + why_it_matters |
| Growth → Memory | memory_candidate.py create | NEVER writes store directly |
| Growth → Career | Write career_handoff JSONL | Future Career Center consumption |

## 13. Security Boundary

- No network, no MCP, no external services
- No secrets stored
- Growth JSONL gitignored
- No direct Memory Store write
- No schema modifications
- No API/Dashboard changes in Task 12-B

## 14. File / Directory Plan

```
growth/{README.md, candidates/, goals/, capacity/, plans/, reviews/, adjustments/, handoffs/, reports/}
scripts/{growth_goal.py, growth_plan.py, growth_review.py}
tests/test_growth_center.py
schemas/examples/{goal_contract, growth_review, capacity_budget, weekly_plan, daily_task}.example.json
```

**Git**: growth/**/*.jsonl + growth/reports/*.json + logs/growth_audit.jsonl → gitignored.

## 15. Task 12-B Build Plan

Create 5 examples, 3 scripts, 1 test file (41+ tests), 1 report. Modify .gitignore. No API/Dashboard/Memory/Research schema changes.

## 16. Acceptance Criteria (41 items)

T1-T6: README + candidate CRUD. T7-T11: goal contract. T12-T14: capacity budget. T15-T18: daily task. T19-T23: growth review + adjustment. T24-T31: handoff + audit + security. T32-T41: regression (all existing suites, startup, governance, schema).

## 17. Future Extensions

Task 13 (Growth API + Dashboard Panel). Task 14 (Career Center).
