# SF-02｜Approval, Proposal & Risk Governance Flow｜审批、提案与风险治理链路

> 本文件补充 Approval Decision 作为独立对象。审批必须有 scope、过期时间、允许动作、数据边界与写入边界。


## 1. 定位

管理所有需要用户确认、审批、拒绝、合并、降噪的动作。原则是：同意类高风险动作必须经过用户，明显低价值或重复提案可以自动拒绝并留痕。

## 2. 主责

- 主责：Coordinator / 总经理 Agent
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- 高风险 workflow 启用
- 删除正式资产
- 修改核心策略
- 开放端口
- 安装未知依赖
- 发送邮件 / 投递简历 / 提交表单
- 自动化生成的 proposal

## 4. 核心对象

- Proposal
- Risk Assessment
- Approval Decision
- Batch Review
- Auto Reject Log

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

1. R3/R4 动作必须审批。
2. 拒绝可以自动化，同意必须可追溯。
3. Proposal 必须分级为 silent_log / auto_reject / batch_review / immediate_review / mandatory_approval。
4. 用户不能被低价值提案淹没。
---

## Engineering Object Binding｜工程对象绑定

流程 02 使用 Proposal State Machine：

```text
draft → pending_review → approved / rejected / auto_rejected / expired → executing → completed / failed / cancelled → archived
```

所有 Proposal 必须符合 `schemas/core/proposal.schema.json`。approved 不代表直接执行，执行前仍需 Action Registry、Permission Profile 和 Schema Validation。

---

## 补充：Approval Decision 对象

Proposal 是“建议做什么”，Approval Decision 是“用户或策略批准了什么范围”。二者必须分开。

Approval Decision 必须记录：

```text
approval_decision_id
proposal_id / action_execution_id
approver
approval_scope
allowed_actions
denied_actions
data_boundary
write_boundary
max_runs
max_cost
max_external_calls
expires_at
revocation_allowed
status
```

硬规则：

```text
1. 批准必须有范围，不能模糊批准。
2. 过期 approval 不得继续授权。
3. 外部现实动作必须 one_time_only 且二次确认。
4. approval 只能授权其 scope 内动作，不能顺带授权其他动作。
```
