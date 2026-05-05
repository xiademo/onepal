# OnePal — 个人 AI 多 Agent 协作平台

**定位**：一个干净重启的个人 AI 多 Agent 协作平台。
**前身**：`personal-assistant`（已冻结归档到 `archive/personal-assistant_20260503`）

## 主架构

| 层 | 说明 |
|----|------|
| **OpenCode Desktop + DeepSeek V4 API** | 主 Agent 引擎 |
| **Dashboard** | 控制中枢 |
| **Coordinator** | 总调度 |
| **Task Tree Engine** | 多 Agent 执行内核 |
| **Memory / Skills / Approval / Timeline** | 治理层 |

### 9 个 Agent

- **coordinator** — 总调度，路由任务
- **memory_curator** — 记忆管理
- **opencode_builder** — 工程执行
- **capability_hr** — 技能招聘与管理
- **automation_input_manager** — 自动化输入处理
- **research_scout** — 信息搜索与情报
- **deep_research_tutor** — 深度研究与解读
- **goal_growth_planner** — 成长规划
- **career_asset_jd_agent** — 职业资产与求职

## 当前阶段

`clean rebuild P0 foundation`

## 快速启动

```bash
# 1. 启动 Dashboard（开发阶段）
# 浏览器直接打开 dashboard/index.html

# 2. 启动 API Server（后续实现）
# py scripts/api_server.py
```
