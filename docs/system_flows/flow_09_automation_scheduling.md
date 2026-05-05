# 流程 09｜Automation Scheduling, Workflow Registry & Reminder Flow｜自动化调度、Workflow 注册与提醒链路

## 1. 定位

管理定时任务、提醒、workflow 调度、自动触发、运行状态和失败处理。它只管什么时候触发什么，不直接做业务判断。

## 2. 主责

- 主责：Agent 5 Automation & Input Manager
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- 提醒任务
- 定时搜索
- 周报生成
- 健康检查
- 备份检查
- 学习复盘
- 求职复盘
- cleanup job

## 4. 核心对象

- Workflow Registry Entry
- Schedule
- Workflow Run
- Failure Handling
- Reminder Event

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

1. workflow 必须注册，未注册不得运行。
2. n8n 启动不等于 workflow 启用。
3. enabled=true 仍必须通过流程 16 Workflow Activation Gate。
4. 高风险 workflow 启用必须审批。
5. 定时任务不能自动执行现实世界动作。
---

## Engineering Object Binding｜工程对象绑定

流程 09 使用 Workflow 和 Workflow Run Schema：

```text
workflow：schemas/core/workflow.schema.json
workflow_run：schemas/core/workflow_run.schema.json
```

Workflow Run 状态机：

```text
scheduled → queued → preflight → running → succeeded / failed / paused / cancelled / timeout → archived / dead_letter
```

n8n 启动不等于 workflow 启用，workflow 必须通过 Workflow Activation Gate。
