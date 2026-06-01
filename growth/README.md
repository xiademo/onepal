# Growth Center

OnePal 目标成长中心。将目标、计划、任务和复盘转化为可执行、可调整的成长计划系统。

## 目录结构

```
growth/
├── README.md
├── candidates/   # 目标候选 (JSONL)
├── goals/        # 目标合约 (JSONL)
├── capacity/     # 容量预算 (JSONL)
├── plans/        # 周计划 + 日任务 (JSONL)
├── tasks/        # 日任务 (JSONL)
├── reviews/      # 成长复盘 (JSONL)
├── adjustments/  # 计划调整提案 (JSONL)
├── handoffs/     # 转交候选 (JSONL)
└── reports/      # 报告 (JSON)
```

## Git 策略

- `growth/README.md` → 允许提交
- `growth/**/.gitkeep` → 允许提交
- `growth/**/*.jsonl` → 不提交
- `growth/reports/*.json` → 不提交

## 相关脚本

- `scripts/growth_goal.py` — 目标候选/合约管理
- `scripts/growth_plan.py` — 容量/周计划/日任务管理
- `scripts/growth_review.py` — 复盘/调整/转交
- `tests/test_growth_center.py` — 自动化测试
