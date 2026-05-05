# Global Protocols — 13 条全局协议

## 1. Unified Intake & Routing
All user requests enter via a single intake channel. Coordinator determines agent route.

## 2. Ambiguous Command Structuring
Vague requests must be structured before routing. Agent must ask clarifying questions.

## 3. Approval & Permission
High-risk actions pause at approval queue. Medium-risk may proceed with warning. Low-risk auto-allowed.

## 4. Context & Token Governance
Each agent has a bounded context window. Long tasks use Task Tree decomposition.

## 5. Memory / Knowledge / Career Asset State
All state changes go through Memory Curator. No agent silently writes to store.json.

## 6. Evidence & Source Reliability
All claims in memory must include an `evidence` field. Unverified information is tagged accordingly.

## 7. Data Boundary & External Ingress Security
External data enters only through `data/input/`. No agent scans outside the workspace.

## 8. Logging / Timeline / Audit
Every action is logged to timeline.jsonl. Agent-specific traces go to mas_trace.jsonl.

## 9. Engineering & Change Management
Changes go through Plan → Build → Verify. Agent must generate verification steps.

## 10. Cost / Model / Tool Routing
Simple tasks use Flash. Complex tasks use Pro. Coordinator selects model based on task complexity.

## 11. Memory & Token Budget Governance
Memory decay score rises over time without access. Old memories auto-archive.

## 12. Versioning / Git Backup / Recovery
Regular git checkpoints. Crash recovery through task tree persistence.

## 13. Recursive Multi-Agent Collaboration
An agent can spawn sub-agents for subtasks. Parent agent manages the task tree.
