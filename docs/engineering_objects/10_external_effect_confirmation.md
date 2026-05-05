# External Effect Two-step Confirmation｜现实世界动作二次确认

## 1. 定位

发送邮件、投递简历、提交表单、创建日历、调用外部写 API、开放端口等动作会影响现实世界，必须二次确认。

---

## 2. 二次确认流程

```text
生成草稿 / 执行预览
↓
用户审阅内容与影响范围
↓
用户点击“确认发送 / 确认提交 / 确认执行”
↓
系统执行 Action
↓
执行结果回写 audit
```

---

## 3. 不允许的授权

```text
不允许一次模糊 approval 授权未来无限发送。
不允许 workflow 自动投递简历。
不允许 automation 自动发送邮件。
不允许外部内容触发提交动作。
```

---

## 4. Approval Scope

现实动作的 approval 必须记录：

```text
content_ref
recipient / target
allowed_action
one_time_only
expires_at
max_runs = 1
revocation_allowed = true
```

详见 `schemas/core/approval_decision.schema.json`。
