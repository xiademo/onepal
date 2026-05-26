# OnePal Task 08-B Memory Center Report

Generated: 2026-05-26

## 1. Verdict

**PASS_READY_FOR_REVIEW**

All 16 memory center tests pass. Memory lifecycle: capture → validate → dedupe → propose → approve → store → archive/supersede. Secret detection active. Forbidden content auto-rejected.

## 2. What Was Built

A file-driven Memory Center as OnePal's long-term memory layer. Two Python scripts implement the full lifecycle, with strict governance integration and security boundaries.

| File | Purpose |
|------|---------|
| `memory/README.md` | Memory Center policy and directory documentation |
| `scripts/memory_candidate.py` | Create, validate, deduplicate, and propose memory candidates |
| `scripts/memory_store.py` | Write approved proposals to store, list, archive, supersede |
| `tests/test_memory_center.py` | 16 automated tests covering full lifecycle |
| `schemas/examples/memory_store.example.json` | Draft memory store entry example |

## 3. Memory Lifecycle

```
create candidate (memory_candidate.py create)
  → validate (schema + secrets + forbidden detection)
  → dedupe (sha256 hash of type + content + source)
  → propose (memory_candidate.py propose)
  → approve (via decide_proposal.py or proposal.status=approved)
  → store (memory_store.py store — only approved proposals)
  → active (listable via memory_store.py list)
  → archive / supersede (memory_store.py archive/supersede)
```

**Rejection gates**:
- Empty content → rejected
- Forbidden sensitivity → rejected
- Secret-like content (API keys, tokens, passwords) → rejected
- Duplicate existing candidate → merged, not duplicated
- Unapproved proposal → blocked from store
- Rejected proposal → blocked from store

## 4. Memory Data Files

| Path | Type | Git? |
|------|------|------|
| `memory/README.md` | Documentation | ✅ Committed |
| `memory/candidates/memory_candidates.jsonl` | Runtime JSONL | ❌ Gitignored |
| `memory/proposals/memory_proposals.jsonl` | Runtime JSONL | ❌ Gitignored |
| `memory/store/memory_store.jsonl` | Runtime JSONL | ❌ Gitignored |
| `memory/archive/memory_archive.jsonl` | Runtime JSONL | ❌ Gitignored |
| `memory/indexes/memory_index.json` | Runtime JSON | ❌ Gitignored |
| `memory/reports/memory_health_report.json` | Runtime JSON | ❌ Gitignored |
| `logs/memory_audit.jsonl` | Audit log | ❌ Gitignored |

## 5. Security Boundary

| Rule | Implementation |
|------|---------------|
| Secret detection | 9 regex patterns: sk-, BEGIN KEY, ghp_, JWT, credit cards, API key, password, token, secret |
| Forbidden sensitivity auto-reject | sensitivity="forbidden" → rejected before proposable |
| All writes require approval | memory_store.py checks proposal.status == "approved" |
| Unapproved proposals blocked | status not "approved" → exit 1 + audit |
| Rejected proposals blocked | status "rejected" → exit 1 + audit |
| Deduplication | sha256(memory_type + content[:100] + source) — same key → merged |
| No dashboard write access | Dashboard reads only via future API, never writes memory directly |
| No API write access (current) | API does not expose memory endpoints yet |
| No secrets in store | T16 validates store contents |

## 6. Test Results

| # | Test | Result |
|---|------|--------|
| T1 | memory/README.md exists | ✅ PASS |
| T2 | Candidate created | ✅ PASS |
| T3 | Candidate JSONL parseable | ✅ PASS |
| T4 | Empty content rejected | ✅ PASS |
| T5 | Forbidden sensitivity rejected | ✅ PASS |
| T6 | Secret content rejected | ✅ PASS |
| T7 | Candidate → proposal | ✅ PASS |
| T8 | Unapproved proposal blocked | ✅ PASS |
| T9 | Approved proposal → store | ✅ PASS |
| T10 | Rejected proposal → not stored | ✅ PASS |
| T11 | Duplicate deduped | ✅ PASS |
| T13 | Archived → not active | ✅ PASS |
| T14 | Superseded retains ref | ✅ PASS |
| T15 | Audit log parseable | ✅ PASS |
| T16 | Store has no secrets | ✅ PASS |
| T17 | Memory JSONL gitignored | ✅ PASS |

**16/16 PASS, 0 FAIL**

## 7. Git Status

```
 M .gitignore
?? memory/README.md (new)
?? schemas/examples/memory_store.example.json (new)
?? scripts/memory_candidate.py (new)
?? scripts/memory_store.py (new)
?? tests/test_memory_center.py (new)
```

## 8. Risks / Open Issues

| Risk | Notes |
|------|-------|
| File-driven MVP | No API integration yet; memory accessed via CLI scripts only |
| No Dashboard Memory panel | Future Task 09+ |
| No vector search | Not in P0 scope |
| No encryption | Memory stored as plaintext JSONL |
| Approval integration minimal | Uses proposal.status field directly; full decide_proposal.py integration future |
| T12 (conflict proposal) | Planned but not yet tested — requires similarity threshold implementation |

## 9. Next Step Recommendation

**Task 08-B Seal Commit** — commit the memory center files, then proceed to Task 09 Planning (API + Dashboard integration).
