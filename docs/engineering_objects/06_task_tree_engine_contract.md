# Task Tree Engine Contract｜任务树执行器契约

## 1. 定位

Task Tree Engine 负责复杂任务拆解、依赖排序、Agent 分派、并行 / 串行执行、失败处理与结果聚合。

它不是审批系统、权限系统、运行环境系统或工具调用系统。

---

## 2. 核心对象

```text
Task Tree：一次复杂任务的树状执行计划。
Task Node：树中的单个任务节点，可映射到 task.schema.json。
Subtask Request：父任务向子任务发出的结构化请求。
Handoff：一个 Agent 向另一个 Agent 移交任务的对象。
```

对应 schema：

```text
schemas/core/task_tree.schema.json
schemas/core/task.schema.json
schemas/core/subtask_request.schema.json
schemas/core/handoff.schema.json
```

---

## 3. Task Packet 最低字段

```text
task_id
parent_task_id
depth
task_owner
agent
objective
input_summary
constraints
expected_output
allowed_actions
token_budget
time_budget
risk_level
stop_conditions
```

---

## 4. 禁止绕过

Task Tree 不得绕过：

```text
Action Registry
Permission Profile
Approval Decision
Workflow Activation Gate
Runtime Lock
Write Mode
Smoke Test
```

---

## 5. 最终硬规则

```text
1. Task Tree 节点不得直接调用工具，只能请求 Action。
2. 任务涉及写正式状态时，必须走 SF-06。
3. 任务涉及启动服务、停止服务、安装依赖、修改端口、启用 workflow、部署更新、回滚恢复时，必须走 SF-16。
4. Handoff 必须记录 from_agent、to_agent、objective、expected_output、risk_level、allowed_actions。
5. Task Tree completed 前必须聚合子任务状态和 output_refs。
```
