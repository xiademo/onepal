# OnePal Task 11 Research API + Dashboard Integration Plan

Status: PLAN_READY_FOR_TASK_11B_BUILD | Generated: 2026-05-26

---

## 1. Purpose

Connect the Research / Cognition Center (Task 10-B) to the API Server (Task 06) and Dashboard (Task 07-B). The API becomes the sole access layer for research operations. The Dashboard gains a 7th Research/Cognition Panel.

## 2. Scope

- 15 Research API endpoints (5 GET, 10 POST)
- Dashboard Research/Cognition Panel (7th panel)
- Secret redaction in API responses
- Memory handoff boundary preserved (no direct store writes)
- 30+ acceptance tests

## 3. Non-Goals

❌ Web scraping / browser automation / MCP
❌ Vector search / RAG
❌ Full article storage
❌ Growth/Career integration (handoffs only)
❌ Core schema modifications

## 4. Current Research Center Baseline

`scripts/research_packet.py` provides: source-create, source-evaluate, source-archive, source-list, packet-create, packet-synthesize, packet-list, evidence-create, handoff-create. `scripts/cognition_card.py` provides: create, list, archive.

**Decision**: API calls these scripts via `subprocess.run()` — same pattern as Memory API (Task 09-B). No script modifications needed.

## 5. API Integration Boundary

```
Dashboard Research Panel
  → fetch() to http://127.0.0.1:18790/research/...
    → api_server.py handler
      → subprocess.run(["py", "scripts/research_packet.py", "source-create", ...])
      → subprocess.run(["py", "scripts/cognition_card.py", "create", ...])
      ← JSON response with redaction
    ← Dashboard renders Research Panel
```

## 6. Research API Contract

### GET endpoints

| Method | Path | Source Script | Limit | Safety |
|--------|------|---------------|-------|--------|
| GET | `/research/sources` | research_packet.py source-list | 20, max 100 | Redacted |
| GET | `/research/packets` | research_packet.py packet-list | 20, max 100 | |
| GET | `/research/evidence` | fixed JSONL reader | 20, max 100 | |
| GET | `/research/cognition-cards` | cognition_card.py list | 20, max 100 | |
| GET | `/research/handoffs` | fixed JSONL reader | 20, max 100 | |

### POST endpoints

| Method | Path | Source Script | Safety |
|--------|------|---------------|--------|
| POST | `/research/sources` | research_packet.py source-create | Secret check, 2000 char limit |
| POST | `/research/sources/evaluate` | research_packet.py source-evaluate | |
| POST | `/research/packets` | research_packet.py packet-create | Source validation |
| POST | `/research/evidence` | research_packet.py evidence-create | |
| POST | `/research/packets/synthesize` | research_packet.py packet-synthesize | |
| POST | `/research/cognition-cards` | cognition_card.py create | |
| POST | `/research/handoffs` | research_packet.py handoff-create | Memory → candidate only |
| POST | `/research/archive` | research_packet.py source-archive / cog card archive | |
| POST | `/research/sources` | Creates source record | |
| POST | `/research/sources/evaluate` | Evaluates source (A/B/C/D trust) | |

## 7. Dashboard Research Panel Design

**7th panel** — full-width, below Memory Center.

### Layout
```
┌──────────────────────────────────────────────────────────────┐
│  Research / Cognition Center                                 │
├──────────────┬───────────────────┬───────────────────────────┤
│ Create Source│ Sources Table     │ Packets Table             │
│ Form         │ (GET /research/   │ (GET /research/packets)   │
│ (POST)       │  sources)         │                           │
│              │ Evaluate Source   │ Evidence Packs            │
│ Result area  │ (POST /evaluate)  │ (GET /research/evidence)  │
│              │                   │                           │
├──────────────┴───────────────────┴───────────────────────────┤
│  Cognition Cards            │  Handoff Candidates            │
│  (GET /cognition-cards)     │  (GET /research/handoffs)      │
│  Create from packet         │  Memory/Growth/Career/Cap      │
└─────────────────────────────┴───────────────────────────────┘
```

### UI States
loading, empty, error, api_unavailable, source_created, source_rejected, source_evaluated, packet_created, evidence_created, synthesis_created, cognition_card_created, handoff_created, archive_success, archive_failed

## 8. Security Boundary

| Rule | Enforcement |
|------|------------|
| 127.0.0.1 only | ✅ API binding |
| No shell=True | ✅ subprocess list form |
| Secret detection | ✅ research_packet.py patterns |
| Content length limit | ✅ 2000 chars |
| No direct Memory write | ✅ Memory handoff → candidate only |
| No network/scraping/MCP | ✅ API code never accesses network |
| Redaction in GET | ✅ Secret content → [REDACTED] |
| No arbitrary paths | ✅ Fixed script paths |
| Dashboard only calls API | ✅ No research/ or script access |

## 9. Data Redaction Rules

Same as Memory: secret patterns → [REDACTED], no local absolute paths in responses, content_summary only for non-owner views.

## 10. Error Handling

| Code | HTTP | Trigger |
|------|------|---------|
| EMPTY_CONTENT | 400 | Empty source content |
| CONTENT_TOO_LONG | 400 | >2000 chars |
| SECRET_DETECTED | 400 | Secret pattern match |
| SOURCE_NOT_FOUND | 404 | Invalid source_id |
| PACKET_NOT_FOUND | 404 | Invalid packet_id |
| MISSING_SOURCE_IDS | 400 | Packet without sources |
| HANDOFF_CREATED | 400 | Memory handoff = candidate only (informational) |
| NOT_FOUND | 404 | Unknown route |
| INTERNAL_ERROR | 500 | Script failure |

## 11. Task 11-B Build Plan

### Files to Modify
```
scripts/api_server.py          — Add 15 research endpoints
tests/test_api_server.py       — Add 34 research API tests (T1-T34)
dashboard/index.html           — Add Research Panel HTML
dashboard/app.js               — Add Research Panel logic
dashboard/style.css            — Add Research Panel styles
tests/test_dashboard_static.py — Add 18 research dashboard tests (T35-T52)
```

### Files to Create
```
docs/reports/task11_research_api_dashboard_report.md
```

### Files NOT to Modify
```
scripts/research_packet.py, scripts/cognition_card.py
scripts/memory_candidate.py, scripts/memory_store.py
schemas/core/*.schema.json, schemas/registry.json
registries/action_registry.json, policies/permission_profiles.json
scripts/request_action.py, decide_proposal.py, check_permission.py
scripts/command_gateway.py, scripts/runtime_runner.py
```

## 12. Task 11-B Acceptance Criteria (34 items)

### API Tests (T1-T34)
T1-T14: GET endpoint read/empty/limit checks. T15-T29: POST endpoint create/validate/reject checks. T30-T34: Safety (no shell=True, no network, JSON response, no arbitrary path, no eval/exec).

### Dashboard Static Tests (T35-T52)
T35: Research Panel exists. T36-T48: All GET/POST endpoints referenced in app.js. T49-T52: No direct research/ access, no script calls, no eval, no CDN.

### Regression (T53-T60)
All existing suites PASS. Startup ready. Governance PASS. Schema PASS. No JSONL leaks.

## 13. Risks / Open Issues

| Risk | Mitigation |
|------|-----------|
| 15 new endpoints increase API server size | Acceptable; follow existing pattern |
| Research scripts CLI output may need formatting | Add minimal --json flag if needed |
| Dashboard panel count now 7 | CSS grid may need layout adjustment |
| Secrets scan false positives from test fixtures | Add research test file exclusions |

## 14. Future Extensions

- Research search / keyword index
- Automated source freshness decay
- Growth/Career center integration (consume handoff JSONL)
- Research analytics dashboard
