# Research / Cognition Center

OnePal 研究与认知拓展中心。将外部资料、用户输入转成可追踪的研究包，并生成认知卡片。

## 目录结构

```
research/
├── README.md
├── sources/      # 研究来源记录 (JSONL, 不提交)
├── packets/      # 研究包 (JSONL, 不提交)
├── evidence/     # 证据包 (JSONL, 不提交)
├── cognition/    # 认知卡片 (JSONL, 不提交)
├── handoffs/     # 转交候选 (JSONL, 不提交)
└── reports/      # 研究报告 (JSON, 不提交)
```

## Git 策略

- `research/README.md` → 允许提交
- `research/**/.gitkeep` → 允许提交
- `research/**/*.jsonl` → 不提交
- `research/reports/*.json` → 不提交

## 生命周期

source → evaluate → packet → evidence → synthesis → cognition card → handoff → archive

## 相关脚本

- `scripts/research_packet.py` — 来源/评估/研究包/证据/转交
- `scripts/cognition_card.py` — 认知卡片
- `tests/test_research_center.py` — 自动化测试
