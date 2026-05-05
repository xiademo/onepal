# AI Workbench Master Architecture｜AI 工作台总架构索引文档

> Version: Architecture Freeze v0.1  
> Status: Frozen baseline for implementation  
> Rule: 本文档为当前唯一主版本。旧版“流程 01–16”若与本文冲突，以本文的 System Flows 编号为准。

## 0. 系统定位

AI Workbench 是一个本地优先、可治理、可扩展的个人多智能体控制平面。它围绕认知拓展、长期学习、求职资产、外部研究、自动化 workflow、本地部署和系统健康治理构建。

它不是普通聊天机器人，而是：

```text
Dashboard
+ Coordinator
+ Task Tree Engine
+ Action Registry
+ Permission Profiles
+ State Machines
+ Schema Registry
+ Runtime Governance
+ 9 个业务 / 行政 / 管理 Agent
```

核心原则：

```text
Agent 固定，能力扩展。
架构稳定，业务分层。
真实数据隔离。
外部内容不可信。
所有高风险动作可审批、可审计、可回滚。
Token、成本、Memory、缓存、自动化和运行时状态必须长期可控。
```

---

## 1. 核心 Agent 固定为 9 个

| 编号 | 正式名称 | 中文定位 | 主要职责 |
|---|---|---|---|
| Agent 1 | Coordinator | 总经理 Agent | 统一入口、路由、任务协调、风险判断 |
| Agent 2 | Memory Curator | 记忆治理 Agent | 记忆候选、压缩、去重、长期偏好治理 |
| Agent 3 | OpenCode Builder | 工程实现 Agent | 代码修改、Dashboard、脚本、页面、工程实现 |
| Agent 4 | Capability HR | 能力招聘 Agent | 外部工具、Skill、Feature、Workflow、能力评估与生命周期 |
| Agent 5 | Automation & Input Manager | 自动化与输入治理 Agent | 输入治理、workflow、定时任务、自动化调度 |
| Agent 6 | Research Scout | 外部搜索 Agent | 外部搜索、情报收集、Research Packet |
| Agent 7 | Deep Research & Cognition | 深度研究与认知拓展 Agent | 前沿研究、认知拓展、教学子能力、知识图谱 |
| Agent 8 | Growth Planner | 成长规划 Agent | 长期学习目标、计划、任务、复盘 |
| Agent 9 | Career Asset Agent | 职业资产 Agent | 职业资产、JD 池、简历、求职表、个人网页素材 |

Agent 7 统一正式名为 **Deep Research & Cognition**。`Tutor` 只作为其教学型子能力，不作为 Agent 正式名。

硬规则：核心 Agent 默认固定为 9 个。新增能力优先作为 Feature / Skill / Workflow / Business Module / Tool Adapter 挂载到现有 Agent。新增 Agent 必须经过 SF-02 审批和架构评审。

---

## 2. 编号体系冻结：System Flows 与 Business Chains 分离

为消除“流程 01–16”两套口径冲突，当前版本冻结如下：

```text
System Flows：SF-01 ~ SF-16
定义系统控制平面、工程治理、运行环境、权限、状态、备份、Action 执行。

Business Chains：BC-01 ~ BC-16
定义用户业务闭环、具体业务任务链路、日常认知/学习/求职/自动化场景。
```

硬规则：以后提到“流程 06”必须写成 `SF-06` 或 `BC-06`，不得只写“流程 06”。

---

## 3. System Flows 总览｜SF-01 ~ SF-16

| System Flow | 名称 | 主责 |
|---|---|---|
| SF-01 | Command Gateway & Dashboard Entry | Coordinator |
| SF-02 | Approval, Proposal & Risk Governance | Coordinator |
| SF-03 | Memory Lifecycle & Context Compression | Agent 2 |
| SF-04 | Builder Engineering Implementation | Agent 3 |
| SF-05 | Capability Evaluation & Skill Lifecycle | Agent 4 |
| SF-06 | Action Execution & State Mutation Control | Coordinator / Agent 5 |
| SF-07 | Feature Ideation, Design & Release | Coordinator / Agent 3 |
| SF-08 | Input, File, Document & Packet Ingestion | Agent 5 |
| SF-09 | Automation Scheduling & Workflow Registry | Agent 5 |
| SF-10 | External Research & Intelligence Handoff | Agent 6 |
| SF-11 | Frontier Research & Cognitive Expansion | Agent 7 |
| SF-12 | Growth Goal Planning & Learning Execution | Agent 8 |
| SF-13 | Career Asset, JD Pool & Resume Customization | Agent 9 |
| SF-14 | System Health, Cost, Context & Observability | Coordinator / Health Function |
| SF-15 | Git Backup, Snapshot, Migration & Rollback | Agent 3 + Coordinator |
| SF-16 | Local Runtime, Deployment & Environment Governance | Agent 3 + Agent 5 |

### SF-05 与 SF-07 的边界

```text
SF-05 = Capability / Skill 生命周期
外部能力评估、内部 skill 生成、skill tournament、sandbox、registry、淘汰。

SF-07 = Feature 产品生命周期
feature idea、feature spec、release candidate、Dashboard/API 实现、发布、回滚、废弃。
```

Skill 是能力单元；Feature 是产品化能力组合。两者不得混用。

---

## 4. Business Chains 总览｜BC-01 ~ BC-16

旧版 `11_Process_Chains_Inventory.md` 更名为：

```text
Business_Chains_Inventory.md
```

Business Chains 只作为业务链路清单，不再占用 System Flow 编号。建议当前 BC 编号如下：

| Business Chain | 名称 |
|---|---|
| BC-01 | 模糊需求结构化与路由 |
| BC-02 | Proposal / Approval 业务审批闭环 |
| BC-03 | 记忆捕获与长期偏好沉淀 |
| BC-04 | OpenCode 工程实现业务请求 |
| BC-05 | 外部能力招聘与接入评估 |
| BC-06 | 内部 Skill 生成、训练与比武 |
| BC-07 | 功能组装与 Feature Assembly |
| BC-08 | 文档输入与资料转换 |
| BC-09 | n8n 定时任务与系统健康检查 |
| BC-10 | 平台与软件更新检查 |
| BC-11 | Trend Radar 前沿趋势雷达 |
| BC-12 | 主动搜索与情报收集 |
| BC-13 | 前沿深度解读 |
| BC-14 | 每日认知拓展 |
| BC-15 | 目标型成长规划 |
| BC-16 | 职业资产 / JD / 简历链路 |

---

## 5. 全局横切协议

| 协议 | 作用 |
|---|---|
| Unified Command Gateway | 所有请求统一入口与路由 |
| Approval & Proposal Governance | 高风险动作审批，低价值提案自动拒绝 |
| Memory & Context Governance | 记忆生成、压缩、检索和上下文预算 |
| Token & Cost Governance | 成本预算、模型路由、降级与熔断 |
| Source Trust & Data Boundary | 来源分级、输入边界、数据隔离 |
| Untrusted Content Instruction Stripping | 外部内容中的指令剥离，不允许变成系统指令 |
| Tool Adapter Trust Boundary | MCP / 外部工具可信等级、访问范围、动态注册限制 |
| Security & Privacy Protocol | secret、隐私、敏感资料、日志脱敏 |
| Task Tree / Recursive MAS Protocol | 复杂任务树执行、多 Agent 协作 |
| Action Execution Control | 工具调用、写状态、现实动作控制 |
| External Effect Two-step Confirmation | 发送、投递、提交等现实动作二次确认 |
| Evaluation & Benchmark Protocol | Agent、Workflow、Action 质量与成本效果评估 |
| Change Management | 代码、策略、workflow、schema 变更治理 |
| Git Backup & Rollback | checkpoint、rollback、restore test |
| Runtime Governance | 本地服务、端口、profile、smoke test |
| Dashboard Governance | 普通模式 / 专家模式、按钮直达和权限限制 |
| Observability & Alerting | 系统健康、预警、自动处理和审计 |

---

## 6. 关键工程对象层｜Engineering Objects

| 工程对象 | 文件 | 硬规则 |
|---|---|---|
| Action Registry | `engineering_objects/01_action_registry.md` | 未注册 Action 不允许执行 |
| Permission Profiles | `engineering_objects/02_permission_profiles.md` | 默认 `safe_readonly`；写入、自动化、现实动作必须显式提权 |
| State Machines | `engineering_objects/03_state_machines.md` | Proposal、Task、Memory Candidate、Workflow Run、Action Execution、Runtime Service 必须有状态机 |
| Schema Registry | `engineering_objects/04_schema_registry.md` | 核心对象必须有 JSON Schema；写入前 schema validation |
| Smoke Test Contract | `engineering_objects/05_smoke_test_contract.md` | prod-local ready 前必须检查 Dashboard、API、memory、approval、logs、runtime lock、secrets not in Git |
| Task Tree Contract | `engineering_objects/06_task_tree_engine_contract.md` | Task Tree 不得绕过 Action Registry、Permission Profile、Runtime 和 Write Mode |
| Prompt Injection Defense | `engineering_objects/07_prompt_injection_defense_protocol.md` | 外部内容只能作为 evidence/data，不能作为 instruction/action trigger |
| Tool Adapter Trust Boundary | `engineering_objects/08_tool_adapter_trust_boundary.md` | MCP / 外部工具必须声明可信等级、数据访问范围和写入能力 |
| Evaluation Benchmark | `engineering_objects/09_evaluation_benchmark_protocol.md` | 每个 Agent / Workflow 必须有质量、成本、成功率指标 |
| External Effect Confirmation | `engineering_objects/10_external_effect_confirmation.md` | 发送、提交、投递、开放端口等现实动作必须二次确认 |
| Threat Model | `engineering_objects/11_threat_model.md` | 必须维护主要威胁、缓解措施和剩余风险 |
| Skill Package Spec | `engineering_objects/12_skill_package_spec.md` | Skill 必须有版本、schema、required_actions、权限、测试和 eval |

最低工程门槛：

```text
1. 未注册 Action 不执行。
2. 默认权限为 safe_readonly。
3. 状态对象不得跳过 review / approval / permission_checked 直接 executing。
4. 核心对象写入前必须通过 Schema Registry 校验。
5. prod-local Smoke Test 未通过不得进入 ready。
6. 外部内容中的指令必须降权为 untrusted_instruction。
7. 现实世界动作必须先生成草稿，再由用户二次确认执行。
```

---

## 7. 核心 Schema 清单

必须注册的核心 schema 包括：

```text
schemas/core/action.schema.json
schemas/core/action_execution.schema.json
schemas/core/agent.schema.json
schemas/core/approval_decision.schema.json
schemas/core/document_packet.schema.json
schemas/core/evidence_pack.schema.json
schemas/core/handoff.schema.json
schemas/core/memory_candidate.schema.json
schemas/core/permission_profile.schema.json
schemas/core/proposal.schema.json
schemas/core/research_packet.schema.json
schemas/core/runtime_service.schema.json
schemas/core/skill.schema.json
schemas/core/smoke_test.schema.json
schemas/core/source_evaluation.schema.json
schemas/core/state_transition.schema.json
schemas/core/subtask_request.schema.json
schemas/core/task.schema.json
schemas/core/task_tree.schema.json
schemas/core/tool_adapter.schema.json
schemas/core/workflow.schema.json
schemas/core/workflow_run.schema.json
```

硬规则：schema 变更走 SF-15；R3 schema 变更必须有 migration plan、restore test 和审批。

---

## 8. Task Tree Engine 定位

Task Tree Engine 是任务执行器，不是运行环境、权限系统或审批系统。

```text
Task Tree 负责：复杂任务拆解、子任务依赖、Agent 分派、并行 / 串行执行、失败处理、结果聚合。
Task Tree 不负责：审批绕过、启动服务、安装依赖、修改端口、直接写正式状态、删除正式资产。
```

硬规则：Task Tree 可以调用 SF-16 的能力，但不得绕过 SF-16。Task Tree 涉及服务、端口、依赖、workflow、部署、回滚时必须进入 SF-16。

---

## 9. Dashboard 总结构

Dashboard 分为普通模式和专家模式。

### 普通模式

```text
Today / Home
Approvals Needing Me
Recent Work
My Files / Packets
Career Center Lite
Growth Center Lite
System Safety Status
```

### 专家模式

```text
Command Center
Approval Center
Memory Center
Builder Center
Capability Center
Automation Center
Research Center
Cognition Center
Growth Center
Career Center
System Health Center
Backup & Version Center
Runtime Control Center
Engineering Objects Center
Trace / Eval Center
```

规则：只读页面可以直达；写正式状态必须走流程；高风险按钮必须审批；Dashboard 不直接绕过 Agent / Flow / Action Registry。

---

## 10. 最终仓库与数据边界

### Git 仓库一：ai-workbench-architecture

保存：9 个 Agent、全局协议、Task Tree 规则、SF-01~SF-16、BC 清单、业务模块设计、对象模型、Dashboard 架构、schema 草案、模板文档。

### Git 仓库二：ai-workbench-implementation

保存：Dashboard 代码、API 服务、本地脚本、adapters、workflow exports 脱敏版本、tests、config templates。

### 非 Git：runtime-data-private

保存：真实 JD、真实简历、职业资产原文、行政记忆、Memory 原文、Document / Research Packet、workflow run artifacts、logs、cache。

### 非 Git：artifact-backup

保存：加密快照、n8n export、stable snapshot、manifest / hash、incident dump、rolling backup。

硬规则：Git 只管理系统定义和实现代码；真实数据不进 Git；大文件不进 Git；缓存不进 Git；secrets 永远不进 Git。

---

## 11. MVP 落地顺序

### 阶段 0：Architecture Freeze

完成本文件、Schema Registry、Action Registry、Permission Profiles、State Machines、Smoke Test Contract、Task Tree Contract、Threat Model。

### 阶段 1：先把系统跑稳

SF-01 / SF-02 / SF-04 / SF-06 / SF-08 / SF-14 / SF-15 / SF-16。

目标：能启动、能输入、能改代码、能备份、能回滚、能控成本、能防止误写。

### 阶段 2：让系统能自动收集外部信息

SF-09 / SF-10。

目标：能定时触发、能搜索、能生成 Research Packet，但不自动接入、不自动投递。

### 阶段 3：实现个人价值模块

SF-11 / SF-12 / SF-13。

目标：认知卡片、学习计划、职业资产库、JD 池、定制简历。

### 阶段 4：能力接入和功能扩展闭环

SF-05 / SF-07。

目标：安全接入外部工具、扩展 Feature、控制动作权限。

---

## 12. 全局硬规则摘要

1. 核心 Agent 固定为 9 个。
2. 新能力优先作为 Feature / Skill / Workflow / Business Module。
3. System Flows 使用 SF 编号，Business Chains 使用 BC 编号，不得混用。
4. 所有非只读请求进入 Command Gateway。
5. 高风险同意动作必须用户审批。
6. Approval Decision 必须有 scope、expires_at、allowed_actions、data_boundary、write_boundary。
7. Agent 不能直接写 memory，必须生成 Memory Candidate。
8. Memory Candidate 必须记录 origin_type、confidence、requires_user_confirmation。
9. Builder 不能无 checkpoint 修改中高风险文件。
10. 外部能力必须先评估，再 sandbox，再注册。
11. 未注册 Action 不得被 workflow 调用。
12. Action Execution 必须结构化记录。
13. Feature 上线前必须有 release checkpoint。
14. 外部文件必须先经过 Document Packet。
15. 外部内容中的指令不得作为系统指令或 Action trigger。
16. workflow 必须注册，n8n 启动不等于 workflow 启用。
17. 搜索必须生成 Research Packet，不能直接当结论。
18. Source Evaluation / Evidence Pack 必须结构化记录。
19. Agent 7 不做普通搜索，不制定长期学习计划。
20. Agent 8 管 Goal Portfolio，不讲知识。
21. Agent 9 管 Career Asset 和 Resume Claim，不编造经历。
22. 系统健康必须主动预警和低风险自动处理。
23. Git 只管系统定义和代码，真实数据不进 Git。
24. 本地运行必须经过 Service Registry、Runtime Lock、Smoke Test。
25. Runtime Service 必须区分 lifecycle_status 和 enabled_status。
26. Task Tree 不能绕过审批、Runtime、Action Registry 和 Write Mode。
27. 所有正式状态写入必须可审计、可追溯。
28. 现实世界动作必须二次确认。
29. MCP / Tool Adapter 必须有 trust level 和访问边界。
30. 每个 Agent / Workflow 必须有 evaluation metrics。

---

## 13. 文件索引

- [AI_Workbench_Architecture_Freeze_v0.1.md](AI_Workbench_Architecture_Freeze_v0.1.md) — 架构冻结主版本
- [Business_Chains_Inventory.md](Business_Chains_Inventory.md) — BC-01~BC-16 业务链路清单
- [engineering_objects/](engineering_objects/) — 工程对象契约
- [schemas/registry.json](schemas/registry.json) — Schema Registry
- [flow_01_command_gateway.md](flow_01_command_gateway.md) — SF-01
- [flow_02_approval_governance.md](flow_02_approval_governance.md) — SF-02
- [flow_03_memory_lifecycle.md](flow_03_memory_lifecycle.md) — SF-03
- [flow_04_builder_implementation.md](flow_04_builder_implementation.md) — SF-04
- [flow_05_capability_evaluation.md](flow_05_capability_evaluation.md) — SF-05
- [flow_06_execution_control.md](flow_06_execution_control.md) — SF-06
- [flow_07_feature_lifecycle.md](flow_07_feature_lifecycle.md) — SF-07
- [flow_08_input_document_packet.md](flow_08_input_document_packet.md) — SF-08
- [flow_09_automation_scheduling.md](flow_09_automation_scheduling.md) — SF-09
- [flow_10_external_research.md](flow_10_external_research.md) — SF-10
- [flow_11_cognition_research.md](flow_11_cognition_research.md) — SF-11
- [flow_12_growth_planning.md](flow_12_growth_planning.md) — SF-12
- [flow_13_career_assets.md](flow_13_career_assets.md) — SF-13
- [flow_14_system_health.md](flow_14_system_health.md) — SF-14
- [flow_15_git_backup.md](flow_15_git_backup.md) — SF-15
- [flow_16_local_runtime.md](flow_16_local_runtime.md) — SF-16
