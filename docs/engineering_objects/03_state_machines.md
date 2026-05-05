# State Machines｜核心对象状态机

## 1. 定位

State Machine 让系统所有核心对象都有明确生命周期，避免出现“任务执行了一半不知道状态”“提案被拒但仍执行”“memory 候选未审批就写入”等工程事故。

统一原则：

```text
对象先 draft，再 review，再 approved / rejected，再 executing，最后 completed / failed / archived。
```

---

## 2. Proposal State Machine

```text
draft → pending_review → approved / rejected / auto_rejected / expired → executing → completed / failed / cancelled → archived
```

硬规则：rejected / auto_rejected / expired 不得进入 executing。

---

## 3. Approval Decision State Machine

```text
draft → pending_review → approved / rejected / expired / revoked → archived
```

硬规则：approval 必须有 scope、allowed_actions、data_boundary、write_boundary、expires_at。过期或撤销后不得继续授权。

---

## 4. Task State Machine

```text
draft → queued → running → blocked / completed / failed / cancelled → archived
```

扩展状态：waiting_approval、waiting_dependency、waiting_user_input、retrying、degraded。

硬规则：running 前必须完成权限检查；completed 必须记录 output_ref 或 completion_summary。

---

## 5. Task Tree / Handoff State Machine

Task Tree：

```text
draft → planned → queued → running → aggregating → completed / failed / cancelled → archived
```

Handoff：

```text
requested → accepted / rejected → running → returned / failed → archived
```

硬规则：handoff 必须有 from_agent、to_agent、input_summary、expected_output、allowed_actions、risk_level。

---

## 6. Memory Candidate State Machine

```text
draft → pending_review → approved / rejected / merged / expired → writing → active / failed → archived / superseded
```

硬规则：Memory Candidate 不能直接写入 active；外部来源或 agent 推断来源默认 requires_user_confirmation=true。

---

## 7. Workflow Run State Machine

```text
scheduled → queued → preflight → running → succeeded / failed / paused / cancelled / timeout → archived / dead_letter
```

硬规则：preflight 必须检查 Workflow Activation Gate。

---

## 8. Action Execution State Machine

```text
requested → registered_checked → permission_checked → schema_validated → waiting_approval / dry_run / executing → completed / failed / rollback_required → rolled_back / archived
```

硬规则：未 permission_checked 不得进入 executing；state_mutation=true 必须写 audit。

---

## 9. Runtime Service State Machine

Runtime Service 拆分两个字段：

```text
lifecycle_status:
registered / starting / healthy / degraded / unhealthy / stopping / stopped / failed

enabled_status:
enabled / disabled
```

硬规则：`enabled_status` 表示配置是否允许启动；`lifecycle_status` 表示运行健康状态。不得把 enabled/disabled 与 healthy/stopped 混在同一个 status 字段。

---

## 10. 最终硬规则

```text
1. Proposal、Approval Decision、Task、Task Tree、Memory Candidate、Workflow Run、Action Execution、Runtime Service 必须有状态机。
2. 状态迁移必须记录 transition log。
3. 不允许绕过 review / permission / preflight 直接 executing。
4. failed / rejected / expired 状态不能继续执行。
5. 所有状态机对象必须有 schema_ref。
6. 任何自动状态迁移必须可审计。
```
