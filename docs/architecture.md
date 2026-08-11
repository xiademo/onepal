# OnePal Architecture

## Current Runtime Note

当前工作台由 `scripts/api_server.py` 仅绑定到 `127.0.0.1` 或 `localhost`，并以固定白名单托管 `/dashboard/`、`/dashboard/style.css` 和 `/dashboard/app.js`。Dashboard 使用同源 API，不授予宽泛 CORS 访问。

远程 OpenAI 兼容模型是受控的提案边界：配置仅保存在 Git 忽略的 `runtime-data-private/model_provider.json`；调用必须经用户点击，输入会进行 secret-like 检测，输出仅显示在页面，不能直接执行命令、写入记忆、启用工具或绕过审批。LiteLLM、MCP、RAG、n8n、LangGraph 与浏览器自动化仍未启用。

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
