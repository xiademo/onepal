# CHANGELOG｜Architecture Freeze

## v0.1.1

本版本针对 v0.1 冻结文档补充 5 个收敛项：

```text
1. 新增“本文档优先级最高”规则：旧版 00_System_Overview、11_Process_Chains_Inventory、AI_Workbench_Master_Architecture 及各 Agent 草案文件降级为历史参考。
2. 第 6 节“必须实现的硬工程对象”补齐 Action Execution Record、Approval Decision、Runtime Service Registry、Workflow Registry。
3. 精确化 Smoke Test ready / limited_ready 判定：critical 全通过且无 warning 为 ready；critical 全通过但存在 warning/skipped 为 limited_ready。
4. runtime_service.schema.json 明确 status 字段废弃或仅兼容；正式字段为 lifecycle_status 与 enabled_status。
5. 新增“冻结后变更规则”：修改冻结主文档必须创建 Architecture Change Proposal；核心规则变更按 R3 处理。
```

## v0.1

初始架构冻结版本：统一 Agent 命名、SF/BC 编号、核心工程对象、核心 Schema 清单、权限/状态/Runtime 最低实现契约。
