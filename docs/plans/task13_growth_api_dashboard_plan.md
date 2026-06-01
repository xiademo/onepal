# OnePal Task 13 Growth API + Dashboard Integration Plan

Status: PLAN_READY_FOR_TASK_13B_BUILD | Generated: 2026-05-31

---

## 1. Purpose

Connect the Growth Center (Task 12-B) to the API Server (Task 06) and Dashboard (Task 07-B). The API becomes the sole access layer for growth operations. The Dashboard gains an 8th Growth Panel.

## 2. Scope

- 20 Growth API endpoints (8 GET + 12 POST)
- Dashboard Growth Panel (8th panel)
- 30+ acceptance tests

## 3. Non-Goals

❌ Calendar/n8n automation, Career Center modification, core schema changes, Growth script changes

## 4. Current Growth Center Baseline

`scripts/growth_goal.py`: candidate-create, accept, reject, goal-create, archive, list.
`scripts/growth_plan.py`: capacity-create, weekly-create, task-create, task-status, list.
`scripts/growth_review.py`: review-create, adjustment-create, memory-handoff, list.

**Decision**: API calls these scripts via `subprocess.run()` — same proven pattern as Memory (Task 09-B) and Research (Task 11-B). Growth scripts need zero modifications.

## 5. API Integration Boundary

```
Dashboard Growth Panel → fetch() → api_server.py → subprocess.run(growth scripts) → growth JSONL
```

## 6. Growth API Contract

### GET (8 endpoints)
| Path | Source |
|------|--------|
| `/growth/candidates` | growth_goal.py list |
| `/growth/goals` | growth_goal.py list |
| `/growth/capacity` | growth_plan.py list |
| `/growth/weekly-plans` | growth_plan.py list |
| `/growth/daily-tasks` | growth_plan.py list |
| `/growth/reviews` | growth_review.py list |
| `/growth/adjustments` | growth_review.py list |
| `/growth/handoffs` | fixed JSONL |

### POST (12 endpoints)
| Path | Script | Safety |
|------|--------|--------|
| `/growth/candidates` | growth_goal.py candidate-create | Secret check, 2000 char |
| `/growth/candidates/accept` | growth_goal.py candidate-accept | |
| `/growth/candidates/reject` | growth_goal.py candidate-reject | |
| `/growth/goals` | growth_goal.py goal-create | success_criteria required |
| `/growth/capacity` | growth_plan.py capacity-create | |
| `/growth/weekly-plans` | growth_plan.py weekly-create | |
| `/growth/daily-tasks` | growth_plan.py task-create | |
| `/growth/daily-tasks/status` | growth_plan.py task-status | |
| `/growth/reviews` | growth_review.py review-create | |
| `/growth/adjustments` | growth_review.py adjustment-create | High impact → approval_required |
| `/growth/handoffs` | growth_review.py memory-handoff | Memory → candidate only |
| `/growth/archive` | growth_goal.py goal-archive | |

## 7. Dashboard Growth Panel Design

8th panel — full-width, below Research Panel. Create Candidate form + Goals table + Capacity + Weekly Plans + Daily Tasks + Reviews + Adjustments.

## 8. Security Boundary

- API delegates via subprocess — never writes files directly
- Dashboard only calls API — no growth/ or script access
- Secret redaction in GET responses
- Memory handoff → candidate only, never writes store directly
- No calendar/n8n, no network/scraping
- 127.0.0.1 only, no arbitrary paths, no shell=True

## 9. Data Redaction Rules

Secret patterns → [REDACTED]. No local absolute paths. Content summary only for non-owner views.

## 10. Error Handling

| Code | HTTP | Trigger |
|------|------|---------|
| EMPTY_TITLE | 400 | Empty candidate title |
| SECRET_DETECTED | 400 | Secret pattern match |
| CANDIDATE_NOT_FOUND | 404 | Invalid candidate_id |
| NOT_ACCEPTED | 400 | Goal from non-accepted |
| MISSING_SUCCESS | 400 | No success_criteria |
| NOT_FOUND | 404 | Unknown route |

## 11. Task 13-B Build Plan

**Modify**: api_server.py (+20 endpoints), tests (API + dashboard), dashboard (HTML + JS + CSS)
**Create**: docs/reports/task13_growth_api_dashboard_report.md
**Do NOT modify**: growth scripts, memory scripts, research scripts, schemas, governance

## 12. Acceptance Criteria (78 items)

T1-T46: API tests (GET empty/list, POST create/validate/reject, safety). T47-T69: Dashboard static tests (panel existence, endpoint usage, no direct access, no eval/CDN). T70-T78: Regression (all suites PASS, smoke ready, governance PASS, schema PASS, no leaks).

## 13. Risks / Open Issues

Growth scripts need zero modifications. API pattern proven. Dashboard panel count now 8. Growth schemas absent (dict-based structures used).

## 14. Future Extensions

Task 14 (Career Center), Task 15 (Growth API + Career integration).
