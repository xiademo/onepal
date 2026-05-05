# 流程 15｜Git Backup, Snapshot, Migration & Rollback Flow｜Git 备份、版本快照、迁移与回滚链路

## 1. 定位

保证代码、配置、workflow、policy、schema、registry、Dashboard 和关键系统定义在变更前后都有 checkpoint、diff、validation、commit、rollback plan、restore test 和审计记录。采用 2 个 Git 仓库 + 2 个非 Git 数据区。

## 2. 主责

- 主责：Agent 3 Builder + Coordinator
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- Builder 修改前
- Policy 修改前
- Workflow 修改前
- Registry/Schema 修改前
- Feature 上线前
- 定时备份
- 异常事件

## 4. 核心对象

- Change Need
- Change Scope
- Backup Eligibility Check
- Pre-change Checkpoint
- Backup Manifest
- Diff Record
- Migration Plan
- Validation Result
- Commit Record
- Rollback Plan
- Restore Test Result

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

1. 初期只建立 ai-workbench-architecture 和 ai-workbench-implementation 两个 Git 仓库。
2. runtime-data-private 和 artifact-backup 不作为 Git 主仓库。
3. Git 不保存敏感原文、大文件、缓存、日志。
4. R2 以上 checkpoint + rollback plan，R3 以上审批 + restore test。
5. 备份必须有 manifest、hash、retention。
