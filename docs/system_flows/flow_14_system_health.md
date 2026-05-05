# 流程 14｜System Health, Cost, Context & Observability Governance Flow｜系统健康、成本、上下文、主动预警与自动处理治理链路

## 1. 定位

监控每个 Agent、workflow、memory、context、cache、proposal、模型调用和运行状态，在 Token 膨胀、成本超限、缓存堆积、workflow 失败、proposal 噪音前主动预警，并对低风险问题自动处理。

## 2. 主责

- 主责：Coordinator + System Health Function
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- 运行指标
- 成本异常
- 上下文膨胀
- workflow 失败
- 缓存堆积
- 低质量 proposal
- 系统资源压力

## 4. 核心对象

- Health Signal
- Metric Snapshot
- Cost Attribution
- Budget Check
- Context Assembly Record
- Alert Event
- Auto Remediation Action
- Optimization Proposal
- Health Report

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

1. 每次上下文装配必须经过 Context Assembly Gateway。
2. 预警分 silent_log / dashboard_warning / batch_review / immediate_alert / emergency_stop。
3. 低风险问题可自动清理、压缩、合并、限流。
4. 正式资产、审计日志、核心策略不得自动删除或修改。
5. Health Check 自身也有预算。
