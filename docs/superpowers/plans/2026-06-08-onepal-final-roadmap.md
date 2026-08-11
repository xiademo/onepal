# OnePal Final Roadmap Implementation Plan

Baseline: `86cdefe feat(growth): add API dashboard integration` on `codex/task-13b-growth-api-dashboard`.

Implementation order:

1. Task 14-A: import builder and memory governance schema pack.
2. Task 14-B: implement Memory Governance v1.5 with review, conflict, change request, and snapshot records.
3. Task 15: implement Career Center v1 with evidence-backed assets, claims, JDs, evaluations, applications, and handoffs.
4. Task 16: implement local Automation/Workflow readiness with disabled workflows and preflight-only runs.
5. Task 17: implement Skill/Capability readiness with disabled candidates and review records.
6. Task 18: implement Knowledge Graph readiness with candidate nodes, edges, boundaries, and RAG-disabled state.
7. Task 19: implement Model/Cost readiness with LiteLLM-disabled routes and local cost events.
8. Task 20: implement MCP/Tool readiness with disabled MCP profiles and write-disabled trust policies.

Safety defaults:

- No dependency install.
- No network access.
- No n8n, LiteLLM, LangGraph, RAG, or MCP enablement.
- No direct memory store writes.
- No external application submission.
- Runtime JSONL remains gitignored.
