# Legacy Summary — 从 personal-assistant 继承的资产

> 旧项目 `D:\git\ai\workspaces\personal-assistant` 已冻结归档到
> `D:\git\ai\workspaces\archive\personal-assistant_20260503`

## 继承的规则

| 规则 | 源文件 | 新项目状态 |
|------|--------|-----------|
| Karpathy 编码规范 | AGENTS.md | ✅ 重写，更精炼 |
| OpenCode Workspace Boundaries | AGENTS.md | ✅ 保持 |
| Memory Update Protocol | AGENTS.md + workflows/memory_update_protocol.md | ✅ 保持 |
| Permission Model | workflows/permissions.json | ✅ 保持 |
| Security Policy | SECURITY.md | ✅ 重写，内容一致 |
| Approval Queue | workflows/approvals.json | ✅ 保持 |
| Feature Configuration Pattern | workflows/features.json | ✅ 保持，等待扩展 |

## 继承的记忆

| 记忆 | 源 | 新项目位置 |
|------|------|-----------|
| 主系统选择 OpenCode + DeepSeek | store.json decision_20260503043320 | memory/decisions.json |
| 用户偏好：先给执行步骤 | store.json user_preference_20260503050957 | memory/preferences.json |
| 用户画像 | memory/USER.md | memory/user_profile.md |

## 没有迁移的

- Dashboard v1/v2 代码（dashboard/ 全部）— 重写
- memory.py — 用 memory_engine.py （后续实现）
- server.py — 用 api_server.py （后续实现）
- feature_runner.py — 合并到 coordinator
- 测试脚本 — 丢弃
- 测试数据 — 丢弃
- convert-to-markdown.ps1 — 按需重新安装
- start-dashboard.bat — 新项目启动方式不同
- OpenCode/ 目录 — 旧项目归档中，新项目需要重新配置
