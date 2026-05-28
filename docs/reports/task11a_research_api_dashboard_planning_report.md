# OnePal Task 11-A Research API + Dashboard Planning Report

Generated: 2026-05-26

## 1. Verdict

**PLAN_READY_FOR_TASK_11B_BUILD** ✅

## 2. What Was Planned

Research API (15 endpoints) + Dashboard Research/Cognition Panel (7th panel). API uses existing research_packet.py/cognition_card.py via subprocess delegation — same proven pattern as Memory API (Task 09-B). Research scripts need zero modifications.

## 3. Files Created

| File | Location |
|------|----------|
| Research API + Dashboard IA Plan (14 sections) | `.omo/plans/task11_research_api_dashboard_plan.md` |
| This Report | `.omo/drafts/task11a_research_api_dashboard_planning_report.md` |

No implementation files created. No API/Dashboard/Research script modifications.

## 4. Existing System Reviewed

| Component | Status | Compatible? |
|-----------|--------|------------|
| research_packet.py (source-create, evaluate, packet-create, etc.) | ✅ Complete | ✅ API can subprocess call |
| cognition_card.py (create, list, archive) | ✅ Complete | ✅ API can subprocess call |
| api_server.py (13 endpoints, Memory pattern) | ✅ Proven | ✅ Research endpoints follow same pattern |
| Dashboard (6 panels, CSS Grid) | ✅ Ready | ✅ Extend with 7th panel |
| Memory API test pattern (Task 09-B) | ✅ Proven | ✅ Reusable for Research API tests |

**Decision**: Research scripts need zero modifications for API compatibility.

## 5. API Contract Summary

| Method | Path | Source Script | Safety |
|--------|------|---------------|--------|
| GET | `/research/sources` | research_packet.py source-list | Read, redacted |
| GET | `/research/packets` | research_packet.py packet-list | Read |
| GET | `/research/evidence` | fixed JSONL | Read |
| GET | `/research/cognition-cards` | cognition_card.py list | Read |
| GET | `/research/handoffs` | fixed JSONL | Read |
| POST | `/research/sources` | research_packet.py source-create | Secret check, 2000 char |
| POST | `/research/sources/evaluate` | research_packet.py source-evaluate | |
| POST | `/research/packets` | research_packet.py packet-create | |
| POST | `/research/evidence` | research_packet.py evidence-create | |
| POST | `/research/packets/synthesize` | research_packet.py packet-synthesize | |
| POST | `/research/cognition-cards` | cognition_card.py create | |
| POST | `/research/handoffs` | research_packet.py handoff-create | Memory → candidate only |
| POST | `/research/archive` | research_packet.py/cognition_card.py | |

**15 total**: 5 GET + 10 POST.

## 6. Dashboard Panel Summary

- **7th panel**: Research / Cognition Center (full-width below Memory Center)
- Create Source form + Sources table + Packets table + Evidence + Cognition Cards + Handoffs
- All data via API — no direct research/ access

## 7. Security Boundary

- API delegates to existing CLI scripts via subprocess — never writes files directly
- Dashboard only calls API — no research/ or script access
- Secret redaction in GET responses
- Memory handoff → candidate only, never writes store directly
- No network/scraping/MCP in API code
- No arbitrary paths, no shell=True
- 127.0.0.1 only

## 8. Verification Results

| Test | Result |
|------|--------|
| test_research_center.py | 31/31 PASS |
| test_memory_center.py | 16/16 PASS |
| test_api_server.py | 35/35 PASS |
| test_dashboard_static.py | 32/32 PASS |
| Git status | Clean ✅ |

114/114 PASS across verified suites.

## 9. Git Status

```
Branch: master, 14 commits, latest: 4e490b2
Status: clean
Only planning documents in .omo/
No implementation files created
```

## 10. Risks / Open Issues

None blocking Task 11-B. Research scripts need no modifications. API pattern proven from Task 09-B.

## 11. Next Step Recommendation

**Task 11-B Build**: Add 15 research endpoints to API server. Add Research Panel to Dashboard. Run acceptance tests. Do NOT modify research scripts.
