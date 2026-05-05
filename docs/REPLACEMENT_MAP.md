# REPLACEMENT MAP｜v0.1.1 补丁替换关系

本补丁基于 `Architecture Freeze v0.1`，用于补齐最终 5 个冻结收敛点。按下表覆盖即可。

## 直接替换文件

| 源文件 | 替换文件 | 变更说明 |
|---|---|---|
| `AI_Workbench_Architecture_Freeze_v0.1.md` | `AI_Workbench_Architecture_Freeze_v0.1.md` | 新增文档优先级最高规则；补齐硬工程对象；精确化 Smoke Test 判定；补 Runtime Service schema 修改要求；新增冻结后变更规则。 |
| `engineering_objects/00_engineering_objects_overview.md` | `engineering_objects/00_engineering_objects_overview.md` | 补齐 Action Execution Record、Approval Decision、Runtime Service Registry、Workflow Registry，并更新硬规则。 |
| `engineering_objects/05_smoke_test_contract.md` | `engineering_objects/05_smoke_test_contract.md` | 明确 ready / limited_ready 判定：critical 全通过且无 warning 为 ready；critical 全通过但有 warning/skipped 为 limited_ready。 |
| `schemas/core/runtime_service.schema.json` | `schemas/core/runtime_service.schema.json` | 保留兼容字段 `status` 并标记 deprecated；正式字段为 `lifecycle_status` 与 `enabled_status`。 |

## 新增文件

| 新增文件 | 作用 |
|---|---|
| `CHANGELOG.md` | 记录冻结版本 v0.1 → v0.1.1 的变更。 |

## 不需要替换的文件

`startup_smoke_test.example.json` 当前已有 warning/skipped 项，因此 `overall_status = limited_ready` 与合同一致，无需替换。

## 操作建议

```text
1. 用本补丁包中的同名文件覆盖原 v0.1 文件。
2. 保留原 v0.1 全量包作为历史备份。
3. 后续实现以 AI_Workbench_Architecture_Freeze_v0.1.md 为最高优先级 source of truth。
4. 任何修改冻结文档的行为，按新第 11 节“冻结后变更规则”处理。
```
