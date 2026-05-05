# 流程 04｜Builder Engineering Implementation Flow｜工程实现与代码变更链路

## 1. 定位

把功能设计、Dashboard、脚本、adapter、workflow runner、页面等落实为代码，同时受 checkpoint、validation、approval、runtime 治理。

## 2. 主责

- 主责：Agent 3 OpenCode Builder
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- 用户要求实现功能
- Feature Release
- 个人网页 / 简历 HTML
- Runtime 页面
- 健康治理页面
- 备份脚本

## 4. 核心对象

- Engineering Request
- Implementation Plan
- Diff Record
- Validation Result
- Build Artifact

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

1. Builder 是实现者，不是审批者。
2. R2 以上代码/配置/schema/workflow 变更必须走流程 15 checkpoint。
3. R3 以上必须流程 02 审批。
4. 未知脚本、外部依赖、正式状态写入不得自动执行。
