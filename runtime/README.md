# Runtime Directory

OnePal 本地运行态目录。所有运行时生成的数据存放在此。

## 目录结构

```
runtime/
├── README.md              # 本文件（可提交 Git）
├── actions/               # 动作执行记录 (JSONL)
├── approvals/             # 提案与审批决定 (JSONL)
├── audit/                 # 状态变更审计 (JSONL)
├── task_trees/            # 任务树运行时状态
├── smoke_tests/           # 启动烟雾测试输出 (JSONL)
├── health_status.json     # 系统健康状态快照
├── runtime_lock.json      # 运行时锁（手动创建）
└── write_mode.json        # 写入模式配置（手动创建）
```

## Git 策略

- `runtime/README.md` → **允许提交**
- `runtime/**/*.jsonl` → **不提交**（.gitignore 已忽略）
- `runtime/health_status.json` → **不提交**
- `runtime/runtime_lock.json` → **不提交**
- `runtime/write_mode.json` → **不提交**
- `runtime/smoke_tests/` → **目录可存在，JSONL 不提交**

## 健康状态说明

`health_status.json` 由 `scripts/run_startup_smoke_test.py` 自动生成。四种状态：

- `ready` — 所有 critical 检查通过，无警告
- `limited_ready` — critical 全部通过，但有非致命警告
- `not_ready` — 存在 critical 失败
- `safe_mode` — 检测到安全边界异常（如 secrets 命中）

## Write Mode 说明

`write_mode.json` 由 `scripts/check_write_mode.py` 读取。四种模式：

- `local_dry_run` — 默认模式，写入被模拟
- `local_write_with_approval` — 审批后可写
- `safe_readonly` — 只读模式
- `locked` — 完全锁定，所有写入和外部访问被拒绝

## Runtime Lock 说明

`runtime_lock.json` 为系统级锁，手动创建。`locked: true` 时系统进入安全模式。
