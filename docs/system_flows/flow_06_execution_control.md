# SF-06｜Action Execution, Tool Use & State Mutation Control Flow｜动作执行、工具调用与状态写入控制链路

> 本文件补充 Action Execution 独立对象与 Tool Adapter Trust Boundary。Action 类型注册不等于一次执行记录。


## 1. 定位

统一管理 Agent、Task Tree、workflow 调用工具、执行脚本、写入状态、调用本地服务时的权限边界。

## 2. 主责

- 主责：Coordinator + Agent 5 Automation & Input Manager
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- Task Tree action node
- workflow 工具调用
- Agent 写状态请求
- runtime action
- engineering action
- real-world action

## 4. 核心对象

- Action Request
- Action Registry Entry
- Permission Check
- Execution Log
- State Mutation Audit

## 5. 标准执行骨架

```text
Intake / Request
↓
Classification / Scope
↓
Risk & Policy Check
↓
Owner Agent Handling
↓
Output / State / Handoff
↓
Audit / Health / Review
```

## 6. Dashboard 对应区域

该流程应在对应 Center 中展示：状态、待处理项、最近运行、风险等级、下一步动作、是否需要审批。

## 7. 关键硬规则

1. 未注册 Action 不得被 workflow 调用。
2. Task Tree 是调度器，不得绕过 Action Registry。
3. 写正式状态必须有审计。
4. real_world_action 必须用户确认。
5. runtime_action 服从流程 16，engineering_action 服从流程 04/15。
---

## Engineering Object Binding｜工程对象绑定

流程 06 必须以 Action Registry 和 Permission Profile 为硬入口。

```text
Action Request
↓
Action Registry Check
↓
Permission Profile Check
↓
Schema Validation
↓
Approval Gate
↓
Action Execution State Machine
↓
Audit / Rollback
```

硬规则：未注册 Action 不得执行；默认权限为 safe_readonly；所有 state_mutation=true 的 Action 必须写入 Runtime Data Write Audit。

---

## 补充：Action Execution 与 Tool Trust

Action Registry 管“动作类型”，Action Execution 管“一次执行实例”。所有执行实例必须写入 `schemas/core/action_execution.schema.json`。

外部工具 / MCP server 必须先登记 Tool Adapter，并声明 trust_level。未验证 MCP server 不得执行写状态、安装依赖、启动服务、开放端口或现实动作。

硬规则：

```text
1. 未注册 Action 不执行。
2. 未记录 Action Execution 的动作视为异常执行。
3. tool trust_level 不满足时，Action 不得进入 executing。
4. external_effect=true 的 Action 必须走二次确认。
```
