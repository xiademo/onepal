# Smoke Test Contract｜启动烟测契约

## 1. 定位

Smoke Test 是系统从“启动了”进入“可用”的最低门槛。

SF-16 中，prod-local 只有通过 smoke test 才能进入 ready。warning 只能进入 limited_ready，critical failure 必须进入 safe-mode 或 not_ready。

---

## 2. 最低 Smoke Test 检查项

```text
Dashboard 能打开
API 能返回 health
memory index 可读
approval queue 可读写
logs 可写
runtime lock 正常
secrets 未进入 Git
Service Registry 可解析
Workflow Registry 可解析
runtime-data-private 可读写
artifact-backup 可写
config drift 可接受
write mode 正确
端口暴露符合规则
policy 文件可解析
secret_ref 存在且未过期
```

---

## 3. 检查等级

```text
critical：失败后不得进入 ready，直接 not_ready 或 safe-mode。
warning：允许 limited_ready，但 Dashboard 必须提示。
info：记录即可，不影响 ready。
```

---

## 4. Ready 判定

```text
ready：所有 critical 均 passed，且不存在 warning / skipped warning。
limited_ready：所有 critical 均 passed，但存在 warning、skipped warning 或非阻塞 degraded 项。
not_ready：至少一个核心服务不可用，且可停留在普通失败态。
safe_mode：存在 critical failure、安全风险、配置漂移高风险或自动化失控风险。
```

硬规则：Smoke Test 示例必须满足：若所有 critical 通过且无 warning，则 `overall_status = ready`；若 critical 通过但存在 warning/skipped，则 `overall_status = limited_ready`。

---

## 5. 输出对象

详见：

```text
schemas/core/smoke_test.schema.json
smoke_tests/startup_smoke_test.example.json
```

---

## 6. 最终硬规则

```text
1. prod-local 启动必须执行 Smoke Test。
2. Smoke Test 未通过不得进入 ready。
3. critical failure 必须进入 safe-mode 或 not_ready。
4. Smoke Test 必须检查 Dashboard、API health、memory index、approval queue、logs、runtime lock、secrets not in Git。
5. Smoke Test 结果必须写入 runtime/smoke_tests.jsonl。
6. 每次部署、回滚、policy 重大变更后必须执行 Smoke Test。
```
