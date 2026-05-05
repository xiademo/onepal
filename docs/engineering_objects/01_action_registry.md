# Action Registry｜可执行动作注册表

## 1. 定位

Action Registry 是所有可执行动作的唯一注册入口。

凡是会读取外部资源、写文件、写状态、调用模型、调用 n8n、发送请求、生成简历、更新 memory、修改 workflow、启动服务、部署代码的动作，都必须先注册为 Action。

一句话：

> **未注册 Action 不允许执行；已注册 Action 也必须经过 Permission Profile、风险等级、审批规则、Schema 校验、Tool Trust Boundary 和审计规则校验。**

---

## 2. Action 执行链路

```text
Agent / Task Tree 意图
↓
Action Request
↓
Action Registry Check
↓
Tool Adapter Trust Check
↓
Permission Profile Check
↓
Schema Validation
↓
Approval / Risk Gate
↓
Execution
↓
Audit / State Machine Update
```

---

## 3. Action 分类

```text
read_only：只读动作，不写状态，不触发现实动作。
local_write：写本地文件或本地状态。
state_mutation：修改 memory、career、growth、workflow、registry 等正式状态。
automation：由定时器、workflow、Task Tree 自动触发。
external_effect：发送邮件、提交表单、调用外部 API、开放端口等现实外部影响。
deployment：安装依赖、启动服务、修改端口、部署更新、回滚。
security_sensitive：secret、权限、webhook、凭证、鉴权相关。
```

---

## 4. input_schema_ref 规则

不是所有 Action 都必须有 `input_schema_ref`。

```text
R0/R1 read_only Action：允许 input_schema_ref = null，但建议补。
R2 及以上 Action：必须有 input_schema_ref。
state_mutation=true：必须有 input_schema_ref。
external_effect=true：必须有 input_schema_ref。
deployment / security_sensitive：必须有 input_schema_ref。
```

硬规则：没有 schema 的高风险 Action 不得执行。

---

## 5. Tool Trust Level

每个 Action 如果依赖工具或 MCP server，必须声明工具可信等级：

```text
trusted_internal_tool
local_sandbox_tool
read_only_external_tool
untrusted_external_tool
mcp_server_verified
mcp_server_unverified
```

工具侧必须声明：

```text
是否联网
是否读取本地文件
是否写本地文件
是否有外部效果
是否返回 prompt-like content
是否可动态注册新工具
是否可访问 secret
```

硬规则：`mcp_server_unverified` 和 `untrusted_external_tool` 不得执行写状态、安装依赖、启动服务、发送邮件、提交表单、开放端口等高风险动作。

---

## 6. 执行前校验顺序

```text
1. Action 是否存在于 Action Registry
2. Action enabled 是否为 true
3. Tool Adapter trust_level 是否允许
4. 当前 profile 是否允许
5. 当前 write_mode 是否允许
6. Permission Profile 是否满足
7. risk_level 是否需要审批
8. 是否需要 input_schema_ref
9. 输入是否通过 schema validation
10. 是否需要 dry_run
11. 是否需要 two-step confirmation
12. 是否需要 idempotency_key
13. 是否需要 Runtime Lock
14. 是否需要 audit log
```

硬规则：任一校验失败，Action 不得进入 executing。

---

## 7. Action Execution 记录

Action Registry 管动作类型；`Action Execution` 管一次实际执行实例。

每次执行必须生成：

```text
action_execution_id
action_id
requester
executor
input_ref
approval_ref
status
started_at / ended_at
error_type
rollback_ref
audit_ref
```

详见 `schemas/core/action_execution.schema.json`。

---

## 8. 默认动作风险等级

| 动作类型 | 默认风险 |
|---|---|
| 只读查询、读取公开配置 | R0 / R1 |
| 写本地草稿、生成文件草稿 | R1 |
| 写正式 memory / career / growth / workflow state | R2 |
| 修改 policy、registry、schema、Agent config | R3 |
| 开放端口、安装系统依赖、启用高风险 workflow | R3 / R4 |
| 删除正式资产、发送邮件、提交表单、外部现实动作 | R3 / R4 |
| 明文 secret 操作、未知脚本、无鉴权公网暴露 | R4，默认拒绝 |

---

## 9. 最终硬规则

```text
1. Task Tree 节点不能直接执行工具，只能请求 Action。
2. 未注册 Action 不执行。
3. 高风险或写状态 Action 必须有 input_schema_ref。
4. 所有 Action Execution 必须写状态机和 audit。
5. 外部现实动作必须走二次确认。
6. untrusted tool 不得写状态、安装依赖、开放端口或执行现实动作。
```
