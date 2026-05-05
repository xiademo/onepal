# 流程 13｜Career Asset, JD Pool & Resume Customization Flow｜职业资产、JD 机会池与简历生成链路

## 1. 定位

建立真实 Career Asset 和 Resume Claim 库，维护职业方向组合与方向简历；JD 进入系统后先评估，只有高价值 JD 才进入“脱颖而出的 JD”并触发定制简历。

## 2. 主责

- 主责：Agent 9 Career Asset Agent
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- 新增职业资产
- 上传 JD
- 搜索 JD
- 生成简历
- 个人网页素材
- 面试反馈

## 4. 核心对象

- Career Asset
- Asset Packaging
- Resume Claim
- Career Direction Portfolio
- JD Item
- JD Evaluation
- Outstanding JD
- Resume Customization Plan
- Customized Resume
- Application Record

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

1. 正式简历只能使用 C2/C3 Resume Claim。
2. 未验证、未完成、设想中的项目不能写成已完成经历。
3. 低价值 JD 不生成定制简历。
4. 不自动投递，不自动标记已投递。
5. 面试反馈必须回流 Resume Claim、Direction Profile、Agent 8。
