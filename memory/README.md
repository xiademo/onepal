# Memory Center

OnePal 长期记忆中心。只保存跨 Agent 可共享的长期结论和用户偏好。

## 目录结构

```
memory/
├── README.md              # 本文件（可提交 Git）
├── candidates/            # 记忆候选 (JSONL, 不提交)
├── proposals/             # 记忆提案 (JSONL, 不提交)
├── store/                 # 已批准记忆 (JSONL, 不提交)
├── archive/               # 已归档记忆 (JSONL, 不提交)
├── indexes/               # 记忆索引 (JSON, 不提交)
└── reports/               # 记忆健康报告 (JSON, 不提交)
```

## Git 策略

- `memory/README.md` → **允许提交**
- `memory/**/.gitkeep` → **允许提交**
- `memory/**/*.jsonl` → **不提交**
- `memory/indexes/*.json` → **不提交**
- `memory/reports/*.json` → **不提交**

## 记忆生命周期

```
capture → validate → dedupe → propose → approve → store → decay → archive
```

## 安全规则

- API key/token/password/secret 自动拒绝
- forbidden sensitivity 自动拒绝
- agent-inferred memory 必须用户确认
- 所有写入必须经过 approval
- 冲突不自动覆盖，生成 conflict proposal

## 相关脚本

- `scripts/memory_candidate.py` — 创建/校验/提案候选记忆
- `scripts/memory_store.py` — 写入/查询/归档/替换记忆
- `tests/test_memory_center.py` — 自动化测试
