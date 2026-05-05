# Threat Model｜威胁模型

## 1. 主要威胁

```text
Prompt Injection：外部内容试图变成系统指令。
Tool Misuse：Agent 越权调用工具。
Permission Drift：权限逐渐扩大。
Memory Poisoning：不可信内容进入长期记忆。
Data Leakage：secret、简历、JD、公司资料进入日志或 Git。
Workflow Runaway：自动化循环执行或连续失败。
Cost Explosion：搜索、深度研究、模型调用成本失控。
Runtime Exposure：Dashboard / n8n / API 暴露到公网。
Schema Drift：字段漂移导致对象无法互操作。
Rollback Failure：备份存在但无法恢复。
```

---

## 2. 主要缓解措施

```text
Action Registry
Permission Profiles
Approval Decision Scope
Prompt Injection Defense
Tool Adapter Trust Boundary
Schema Registry
Runtime Lock
Workflow Activation Gate
Smoke Test
Git Secret Scan
Backup Restore Test
System Health Alerting
```

---

## 3. 剩余风险

```text
1. 用户主动批准错误动作仍可能造成损失。
2. 本地依赖供应链仍需人工判断。
3. 未验证外部工具可能返回恶意内容。
4. 大模型可能误判风险等级。
5. 备份加密密钥丢失会影响恢复。
```

---

## 4. 硬规则

```text
Threat Model 每次 R3 架构变更后必须复查。
新增工具、新增外部连接、新增自动化写入时必须更新威胁模型。
```
