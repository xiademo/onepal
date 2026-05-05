# 流程 01｜Command Gateway & Dashboard Entry Flow｜统一入口与命令分流链路

## 1. 定位

把用户输入、Dashboard 点击、定时触发、文件上传、Agent 内部移交统一归一为 Command Request，并完成意图识别、风险分级、目标流程路由、是否进入 Task Tree 的判断。

## 2. 主责

- 主责：Coordinator / 总经理 Agent
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- 用户自然语言输入
- Dashboard 按钮点击
- 文件 / JD / 链接上传
- 定时任务回调
- Task Tree 子节点请求
- 系统健康预警

## 4. 核心对象

- Command Request
- Routing Decision
- Direct Dashboard Action
- Task Tree Request
- Routing Log

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

1. 只读 Dashboard 页面可以直达；写正式状态、高风险动作、现实动作必须回到 Command Gateway。
2. 复杂跨 Agent 任务进入 Task Tree，但 Task Tree 不能绕过审批、Runtime、Action Registry。
3. 所有非只读请求必须记录 routing log。
