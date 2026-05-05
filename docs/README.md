# AI Workbench Architecture Freeze v0.1

本包是 AI Workbench / 个人 Agent OS 控制平面的架构冻结版本。

## 核心变化

```text
1. System Flows 使用 SF-01~SF-16。
2. Business Chains 使用 BC-01~BC-16。
3. Agent 7 正式名统一为 Deep Research & Cognition。
4. 补齐 Action Execution、Approval Decision、Task Tree、Skill、Document Packet、Research Packet 等 schema。
5. 补齐 Prompt Injection Defense、Tool Adapter Trust Boundary、Evaluation Benchmark、External Effect Confirmation、Threat Model。
6. Runtime Service 拆分 lifecycle_status 与 enabled_status。
7. Smoke Test 示例与 ready / limited_ready 判定保持一致。
```

## 主文件

- `AI_Workbench_Master_Architecture.md`：总架构索引
- `AI_Workbench_Architecture_Freeze_v0.1.md`：冻结版本主文档
- `Business_Chains_Inventory.md`：业务链路清单
- `engineering_objects/`：硬工程对象契约
- `schemas/registry.json`：Schema Registry

## 使用规则

```text
先读 AI_Workbench_Architecture_Freeze_v0.1.md。
实现时以 SF 编号为系统流程，以 BC 编号为业务链路。
新增对象必须先补 schema。
新增动作必须先进入 Action Registry。
写状态必须经过 Permission Profile、State Machine、Schema Validation 和 Audit。
```
