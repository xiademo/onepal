# SF-07｜Feature Ideation, Design & Release Flow｜功能构想、设计与发布链路

> 本文件只负责 Feature 产品生命周期。Skill 生命周期归 SF-05。Feature 是多个 Skill / Action / Workflow / UI 的产品化组合。


## 1. 定位

把想法、搜索结论、用户需求、Agent 建议转化为 Feature，并完成立项、PRD、范围、验收、上线与回收。

## 2. 主责

- 主责：Coordinator + Agent 3 Builder
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- 用户提出功能
- 流程 10 搜索结论
- 流程 05 能力建议
- 流程 11 前沿启发
- 流程 13 个人网页需求

## 4. 核心对象

- Feature Candidate
- Feature Spec
- Release Candidate
- Feature Registry Entry
- Deprecation Plan

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

1. 新需求优先作为 Feature，不默认新增 Agent。
2. Feature 不直接接入外部能力，需流程 05。
3. Feature 不直接实现代码，需流程 04。
4. 上线前必须有 release checkpoint、owner_agent、rollback plan。

---

## 补充：Feature 与 Skill 的区别

```text
Skill：可复用能力包，有输入/输出 schema、required_actions、权限、测试、eval。
Feature：面向用户的产品功能，可能组合多个 Skill、Action、Workflow、Dashboard 页面和业务对象。
```

Feature 上线前必须检查：

```text
1. 所需 Skill 已 enabled。
2. 所需 Action 已注册。
3. 所需 Workflow 已注册但默认不自动启用。
4. Dashboard 入口受 Permission Profile 控制。
5. Release checkpoint 已生成。
6. 回滚方案存在。
```
