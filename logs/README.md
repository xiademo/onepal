# Logs Directory

OnePal 日志目录。

## 文件说明

- `mas_trace.jsonl` — MAS Trace 日志（Multi-Agent System trace）。记录完整的 command → routing → task_tree → action_execution 链路。
- `errors.jsonl` — 运行时错误日志
- `timeline.jsonl` — 时间线日志

## Git 策略

- `logs/README.md` → **允许提交**
- `logs/*.jsonl` → **不提交**（.gitignore 已忽略）
- `logs/**/*.jsonl` → **不提交**

## MAS Trace 说明

MAS Trace 由 `scripts/command_gateway.py` 自动写入，记录以下事件：
- `command_received` — 命令接收
- `routed` — 路由决策生成
- `task_tree_created` — 任务树创建
- `action_execution_*` — 动作执行记录（由 request_action.py 写入）

请勿将真实敏感数据写入日志目录。
