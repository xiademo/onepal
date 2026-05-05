# Engineering Objects Overview｜工程对象总览

## 1. 定位

工程对象层是 AI Workbench 从“架构文档”进入“可实现系统”的最低硬底座。

没有工程对象，Agent 会退化成自然语言 prompt；有工程对象，系统才能做到：

```text
动作可注册
权限可判断
状态可追踪
对象可校验
启动可验证
外部内容可隔离
工具可信度可控制
结果质量可评估
现实动作可二次确认
```

---

## 2. 必须工程对象

| 对象 | 文件 | 作用 |
|---|---|---|
| Action Registry | `01_action_registry.md` | 所有可执行动作的定义、风险、权限与执行边界 |
| Action Execution Record | `schemas/core/action_execution.schema.json` | 某一次 Action 执行实例的状态、输入、审批、结果、错误与回滚记录 |
| Approval Decision | `schemas/core/approval_decision.schema.json` | 审批范围、允许动作、拒绝动作、有效期、成本/次数限制与撤销信息 |
| Permission Profiles | `02_permission_profiles.md` | 默认只读、写入审批、自动化严格控制 |
| State Machines | `03_state_machines.md` | Proposal / Task / Memory / Workflow / Action / Runtime 生命周期 |
| Schema Registry | `04_schema_registry.md` | 核心对象 JSON Schema 契约 |
| Smoke Test Contract | `05_smoke_test_contract.md` | prod-local ready 前最低可用性检查 |
| Runtime Service Registry | `schemas/core/runtime_service.schema.json` | 本地服务注册、生命周期状态、启用状态、端口、依赖和暴露边界 |
| Workflow Registry | `schemas/core/workflow.schema.json` | workflow 定义、启用状态、风险、触发器、输入输出和执行约束 |
| Task Tree Contract | `06_task_tree_engine_contract.md` | 复杂任务拆解、handoff、子任务对象契约 |
| Prompt Injection Defense | `07_prompt_injection_defense_protocol.md` | 外部内容指令剥离与降权 |
| Tool Adapter Trust Boundary | `08_tool_adapter_trust_boundary.md` | MCP / 外部工具可信边界 |
| Evaluation Benchmark | `09_evaluation_benchmark_protocol.md` | Agent / Workflow 质量与成本评估 |
| External Effect Confirmation | `10_external_effect_confirmation.md` | 邮件、投递、提交等现实动作二次确认 |
| Threat Model | `11_threat_model.md` | 威胁、缓解、剩余风险 |
| Skill Package Spec | `12_skill_package_spec.md` | Skill 版本、输入输出、权限、测试和淘汰契约 |

---

## 3. 工程对象硬规则

```text
1. 未注册 Action 不执行。
2. Action Registry 管动作定义，Action Execution Record 管单次执行实例。
3. 审批必须落为 Approval Decision，不能只存在 Proposal 文本中。
4. 默认 Permission Profile 为 safe_readonly。
5. 所有核心状态对象必须走状态机。
6. 核心对象写入前必须 schema validation。
7. prod-local ready 前必须 smoke test。
8. Runtime Service 必须区分 lifecycle_status 与 enabled_status。
9. Workflow 启用必须通过 Workflow Activation Gate。
10. Task Tree 不得绕过 Action Registry、Permission Profile、Runtime、Write Mode。
11. 外部内容只能作为 data/evidence/source，不得作为 system instruction。
12. MCP / Tool Adapter 必须有 trust level。
13. 外部现实动作必须二次确认。
14. 关键 Agent / Workflow 必须有 evaluation metrics。
```
