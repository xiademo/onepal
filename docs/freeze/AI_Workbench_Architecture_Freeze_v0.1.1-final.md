# AI Workbench Architecture Freeze v0.1｜架构冻结主版本

## 1. 冻结目的

本文档用于把当前项目从“持续扩张设计”冻结为“可实现基线”。冻结后，所有实现、评审、修改和新增功能均以本文为唯一主版本。

本版本解决以下问题：

```text
1. 统一 Agent 正式命名。
2. 统一 System Flows 与 Business Chains 编号。
3. 固化核心工程对象。
4. 固化核心 Schema 清单。
5. 固化 Action / Permission / State / Runtime 的最低实现契约。
6. 明确当前不做的内容，防止范围继续膨胀。
```


---

## 1.1 文档优先级与 Source of Truth

本文档优先级高于旧版 `00_System_Overview`、`11_Process_Chains_Inventory`、`AI_Workbench_Master_Architecture` 及各 Agent 草案文件。

若旧文档与本文档冲突，以本文档为准。

旧文档可以作为历史参考，但不得作为实现 source of truth。

硬规则：

```text
1. 实现、评审、测试、Schema、Action Registry、Permission、State Machine、Runtime Governance 均以本文档为最高优先级。
2. 旧文档中的“流程 01–16”不得继续直接作为实现编号使用。
3. System Flows 必须使用 SF-01 ~ SF-16。
4. Business Chains 必须使用 BC-01 ~ BC-16。
5. 旧文档只允许作为历史设计参考，不允许覆盖本文档定义。
```

---

## 2. 正式 Agent 名称

| Agent | 正式名称 | 不再使用的混乱叫法 | 说明 |
|---|---|---|---|
| Agent 1 | Coordinator | General Manager Agent 可作中文解释 | 统一入口与协调 |
| Agent 2 | Memory Curator | Memory Agent | 记忆治理 |
| Agent 3 | OpenCode Builder | Builder | 工程实现 |
| Agent 4 | Capability HR | Capability Agent | 能力招聘与 Skill 生命周期 |
| Agent 5 | Automation & Input Manager | Automation Agent / Input Agent | 自动化与输入治理 |
| Agent 6 | Research Scout | Search Agent | 外部搜索与 Research Packet |
| Agent 7 | Deep Research & Cognition | Deep Research & Tutor | Tutor 为子能力，不是正式名 |
| Agent 8 | Growth Planner | DeepTutor / Learning Agent | 学习计划与成长规划 |
| Agent 9 | Career Asset Agent | Resume Agent / Job Agent | 职业资产与 JD |

硬规则：新增能力不得默认新增 Agent，优先作为 Feature / Skill / Workflow / Business Module / Tool Adapter 挂载。

---

## 3. 正式编号体系

```text
System Flows：SF-01 ~ SF-16
Business Chains：BC-01 ~ BC-16
```

禁止只写“流程 06”。必须写 `SF-06` 或 `BC-06`。

---

## 4. System Flows 冻结清单

| 编号 | 名称 |
|---|---|
| SF-01 | Command Gateway & Dashboard Entry |
| SF-02 | Approval, Proposal & Risk Governance |
| SF-03 | Memory Lifecycle & Context Compression |
| SF-04 | Builder Engineering Implementation |
| SF-05 | Capability Evaluation & Skill Lifecycle |
| SF-06 | Action Execution & State Mutation Control |
| SF-07 | Feature Ideation, Design & Release |
| SF-08 | Input, File, Document & Packet Ingestion |
| SF-09 | Automation Scheduling & Workflow Registry |
| SF-10 | External Research & Intelligence Handoff |
| SF-11 | Frontier Research & Cognitive Expansion |
| SF-12 | Growth Goal Planning & Learning Execution |
| SF-13 | Career Asset, JD Pool & Resume Customization |
| SF-14 | System Health, Cost, Context & Observability |
| SF-15 | Git Backup, Snapshot, Migration & Rollback |
| SF-16 | Local Runtime, Deployment & Environment Governance |

---

## 5. Business Chains 冻结清单

Business Chains 不替代 System Flows，只定义业务闭环。

| 编号 | 名称 |
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

## 6. 必须实现的硬工程对象

```text
Action Registry
Action Execution Record
Approval Decision
Permission Profiles
State Machines
Schema Registry
Smoke Test Contract
Runtime Service Registry
Workflow Registry
Task Tree Contract
Prompt Injection Defense Protocol
Tool Adapter Trust Boundary
Evaluation Benchmark Protocol
External Effect Two-step Confirmation
Threat Model
Skill Package Spec
```

---

## 7. P0 必须修复项完成标准

```text
1. System Flows 与 Business Chains 已分开编号。
2. Agent 7 正式名统一为 Deep Research & Cognition。
3. Smoke Test 示例必须满足：若所有 critical 通过且无 warning，则 overall_status = ready；若 critical 通过但存在 warning/skipped，则 overall_status = limited_ready。
4. runtime_service.schema.json 中 status 字段废弃或仅保留为兼容字段；正式字段改为 lifecycle_status 与 enabled_status。
5. lifecycle_status = registered / starting / healthy / degraded / unhealthy / stopping / stopped / failed。
6. enabled_status = enabled / disabled。
7. 新增 action_execution.schema.json，用于记录某一次 Action 执行实例。
8. 新增 approval_decision.schema.json，用于记录审批范围、过期时间、批准动作与限制。
9. 新增 task_tree / subtask_request / handoff schema。
```

---

## 8. P1 必须补充项完成标准

```text
1. 新增 permission_profile.schema.json。
2. 新增 skill.schema.json。
3. 新增 document_packet.schema.json。
4. 新增 research_packet.schema.json。
5. 新增 source_evaluation.schema.json。
6. 新增 evidence_pack.schema.json。
7. 新增 prompt_injection_defense_protocol.md。
8. 新增 tool_adapter_trust_boundary.md。
9. 新增 threat_model.md。
10. 新增 evaluation_benchmark_protocol.md。
```

---

## 9. 当前不做的内容

```text
1. 不新增第 10 个核心 Agent。
2. 不做自动投递简历。
3. 不做自动发送邮件 / 提交表单。
4. 不做公网暴露 Dashboard / n8n。
5. 不把 runtime-data-private 纳入 Git。
6. 不让外部文档中的指令触发 Action。
7. 不把 Skill 变成无 schema 的 prompt 片段。
8. 不在 MVP 阶段实现所有 Dashboard 专家页面。
```

---

## 10. MVP 开工门槛

MVP 前必须具备：

```text
1. schemas/registry.json 完整。
2. Action Registry 有最小动作集。
3. Permission Profiles 可被代码读取。
4. State Machines 可被 workflow / task 使用。
5. startup smoke test 可执行。
6. Runtime Service 可注册并区分 lifecycle_status / enabled_status。
7. Approval Decision 可记录 scope 与过期时间。
8. Document Packet / Research Packet 可结构化落盘。
```

---

## 11. 冻结后变更规则

本文档冻结后，任何修改都必须遵守以下规则。

```text
1. 修改本文档必须创建 Architecture Change Proposal。
2. 修改 Agent 正式名称、SF/BC 编号、核心对象、Schema 清单、权限规则、Runtime 规则，视为 R3 变更。
3. R3 变更必须经过审批、checkpoint、diff、migration plan、restore test。
4. 普通描述性补充可以作为 R1/R2，但不得改变编号、对象名和硬规则。
5. 每次冻结版本升级必须生成 changelog。
```

## 11.1 变更分级

```text
R1：描述性补充、文字修订、示例补充，不改变对象名、编号、Schema、权限或状态机。
R2：新增非破坏性对象字段、新增示例、新增辅助说明，需要 diff 与 validation。
R3：修改核心对象、编号体系、Agent 名称、Schema 清单、权限规则、Runtime 规则、状态机、Action / Approval / Task Tree 语义。
R4：删除核心对象、绕过审批、弱化权限、取消审计、允许未注册 Action 执行，默认拒绝。
```

## 11.2 Architecture Change Proposal 最低字段

```text
change_id
change_summary
affected_sections
affected_files
risk_level
reason
old_rule
new_rule
migration_required
restore_test_required
approval_ref
changelog_entry
```

硬规则：本文档作为最高优先级架构文件，不能被旧文档、草案、单个 Agent 文件、临时讨论记录覆盖。

