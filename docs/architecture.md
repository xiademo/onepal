# OnePal Architecture

## Overview

```
                   ┌──────────────────────────┐
                   │       Dashboard           │
                   │  (Control Center)         │
                   └────────────┬─────────────┘
                                │
                   ┌────────────▼─────────────┐
                   │       Coordinator         │
                   │    (Task Dispatcher)      │
                   └────────────┬─────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                      │
          ▼                     ▼                      ▼
   ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐
   │  Task Tree  │    │  Approval    │    │   Memory         │
   │  Engine     │    │  Queue       │    │   Curator        │
   └─────────────┘    └──────────────┘    └──────────────────┘
          │                     │                      │
          ▼                     ▼                      ▼
   ┌─────────────────────────────────────────────────────────┐
   │                    9 Agents                              │
   │  coordinator / memory_curator / opencode_builder        │
   │  capability_hr / automation_input_manager              │
   │  research_scout / deep_research_tutor                  │
   │  goal_growth_planner / career_asset_jd_agent           │
   └─────────────────────────────────────────────────────────┘
```

## Layers

| Layer | Component | Responsibility |
|-------|-----------|---------------|
| **Presentation** | Dashboard | Web UI, 7 modules |
| **Orchestration** | Coordinator | Route tasks, dispatch to agents |
| **Execution** | Task Tree Engine | Decompose tasks, track progress |
| **Governance** | Approval Queue | Risk control, permission checks |
| **Memory** | Memory Curator | Store, propose, approve, decay |
| **Capabilities** | 9 Agents | Domain-specific execution |
| **Registry** | Skills / Permissions | Capability catalog, access control |
| **Observability** | Timeline / MAS Trace | Audit trail, debugging |

## Data Flow

1. User request → Dashboard or CLI
2. Coordinator receives → determines agent from route table
3. Task decomposed → Task Tree Engine
4. If high risk → Approval Queue pause
5. Agent executes → writes output + timeline record
6. Memory Curator updates proposals
7. MAS Trace records which agent did what
