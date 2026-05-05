# Permission Profiles｜权限画像

## 1. 定位

Permission Profile 定义系统在不同环境、不同动作、不同风险等级下的最低权限边界。

默认原则：

> **默认只读；写入要受控；自动化要严格审批；现实世界动作必须人工二次确认。**

---

## 2. 基础权限

## 2.1 safe_readonly

默认权限。适用于普通对话、规划、分析、只读查询。

允许：读取已授权架构文档、读取脱敏 summary / manifest、读取 registry / schema / policy、生成草稿、生成 proposal draft、执行 dry run。

禁止：写正式文件、写 memory、写 career/growth/cognition 正式状态、运行 n8n workflow、发送邮件/提交表单、下载外部文件、安装依赖、修改 Git/policy/registry、启动/停止服务、开放端口。

---

## 2.2 local_write_with_approval

本地写入权限。适用于经过审批的文件生成、状态更新、草稿落盘、低风险本地操作。

限制：正式状态写入必须有审批或白名单；必须写 Runtime Data Write Audit；必须受 Write Mode 限制；必须支持 rollback 或明确不可回滚原因。

---

## 2.3 automation_with_strict_approval

严格自动化权限。适用于已注册、已审批、可审计、可限流的 workflow 和定时任务。

强制要求：Action 必须注册；workflow 必须注册；profile 必须允许；Workflow Activation Gate 必须通过；rate limit 必须存在；audit log 必须开启；连续失败必须自动暂停或降级。

禁止：自动发送邮件、自动投递简历、自动提交表单、自动删除正式资产、自动修改核心 policy、自动开放 webhook、自动安装依赖、自动写入未审批 memory。

---

## 2.4 admin_break_glass

事故恢复权限，不作为常规运行权限。

要求：必须人工确认、必须有 reason、必须有 expires_at、必须写 incident log、必须写 rollback plan。

---

## 3. 审批范围

权限提升必须记录：

```text
scope
reason
expires_at
allowed_actions
denied_actions
data_boundary
write_boundary
max_runs
max_cost
revocation_allowed
```

详见 `schemas/core/approval_decision.schema.json`。

---

## 4. Schema

Permission Profile 自身必须通过：

```text
schemas/core/permission_profile.schema.json
```

禁止在 permission profile 中自由混用字段类型。若字段需要表达“禁止 / 允许 / 审批后允许 / 白名单允许”，必须使用枚举值。

---

## 5. 最终硬规则

```text
1. 系统默认 Permission Profile 为 safe_readonly。
2. 所有写入动作必须显式提升权限。
3. 权限提升必须有 scope、reason、expires_at。
4. local_write_with_approval 不能绕过审批写正式状态。
5. automation_with_strict_approval 只能执行已注册、已批准、可审计、可限流的自动化。
6. 现实世界动作必须用户二次确认，不能由 automation 自动执行。
7. 权限判断必须发生在 Action 执行前。
8. Permission Profile 不得被 local config 覆盖。
```
