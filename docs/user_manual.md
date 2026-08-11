# OnePal 本地个人助手使用说明书

## 1. 它现在能做什么

OnePal 当前是一个本地优先的个人 AI Workbench。除非你在工作台中明确点击远程模型检测或提案助手，否则它不会联网；它不会自动投递、不会启用 MCP server，也不会直接写长期 memory store。它通过本地 API + Dashboard 管理这些工作区：

- Health：查看本地系统健康状态。
- Command：提交受治理的本地命令意图。
- Tasks / Runs / Trace：查看任务、运行记录和执行轨迹。
- 记忆：创建候选记忆、提案、审批写入、归档，并查看质量评审、冲突、变更请求和快照。
- 研究：登记资料摘要、证据包、认知卡片和交接记录。
- 成长：目标候选、目标、容量、周计划、日任务、复盘和调整。
- 职业：职业资产、简历证据、JD、JD 评估、申请记录和交接记录。
- Automation / Skills / Knowledge / Model / MCP：只做本地 readiness、候选和配置展示；默认不执行高风险动作。
- 连接设置 / 提案助手：可连接你明确配置的 OpenAI 兼容远程服务，只生成中文建议，不会执行命令、写入记忆或启用外部工具。

## 2. 启动

在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_onepal.ps1
```

脚本会做三件事：

1. 运行 startup smoke test。
2. 启动本地 API：`http://127.0.0.1:18790`。
3. 打开同源 Dashboard：`http://127.0.0.1:18790/dashboard/`。

启动脚本会自动寻找可用 Python：先试 `py`，再试 `python`，最后试 Codex bundled Python。你也可以显式指定：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_onepal.ps1 -Python "C:\Path\To\python.exe"
```

如果你只想启动 API，不自动打开浏览器：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_onepal.ps1 -NoBrowser
```

如果只是本地调试，想跳过启动前 smoke：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_onepal.ps1 -SkipSmoke
```

## 3. 停止

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop_onepal.ps1
```

如果进程卡住：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop_onepal.ps1 -Force
```

## 4. 日常使用路径

推荐从 Dashboard 使用：

1. 打开 Dashboard 后先看“健康状态”，确认本地服务在线。
2. 用 Memory panel 记录项目决策、偏好或长期事实。不要直接改 `memory/store.json` 或 runtime 文件。
3. 用 Research panel 录入资料摘要，再生成 evidence/cognition/handoff。
4. 用 Growth panel 管理目标、周计划、日任务和复盘。
5. 用 Career panel 管理简历证据、JD 匹配和人工申请记录。
6. Automation、Skills、Knowledge、Model、MCP 面板目前用于准备和审查，不代表已经启用自动化或外部工具。

## 5. 远程模型提案助手

1. 在“连接设置”面板填写 HTTPS Base URL，例如 `https://provider.example/v1`。不要填写完整的 `/chat/completions` 地址。
2. 填写模型名称、API Key；输入/输出单价和月度预算是可选项。点击“保存本机配置”不会发起远程请求。
3. 点击“检测远程连接”时，OnePal 才会向 `<Base URL>/models` 发送带 Bearer 认证的连通性请求。
4. 打开“模型 / 成本”，输入需要分析的内容，勾选“我确认本次内容将发送到已配置的远程模型服务”，再点击“生成提案”。
5. 助手的输出固定为“摘要、建议步骤、风险与未知、需要人工确认”四段，只显示在当前页面。需要保存的内容必须由你手动录入 Memory、Research、Growth 或 Career 的既有受治理流程。

安全说明：

- 配置保存到 `runtime-data-private/model_provider.json`，该目录被 Git 忽略。API Key 不会回传到浏览器、不写入日志、健康报告或成本事件。
- 只接受 HTTPS Base URL；请求内容最长 4000 个字符，超时 45 秒，单次最大输出 1200 tokens。
- 检测到疑似 API Key、令牌、密码或私钥的输入会在本机拒绝，不会发送到远程服务。
- 达到月度预算后会拒绝新的提案请求。未配置价格时成本按 `$0` 记录并显示“未配置价格”。

## 6. 常用命令

健康检查：

```powershell
py scripts/run_startup_smoke_test.py
```

如果 `py` 不可用，把上面的 `py` 换成启动脚本打印出来的 Python 路径。

Schema 检查：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate_schema_registry.ps1
```

治理 smoke：

```powershell
py scripts/run_governance_smoke_test.py
```

直接启动 API：

```powershell
py scripts/api_server.py --host 127.0.0.1 --port 18790
```

## 7. 数据和安全边界

- API 只允许绑定 `127.0.0.1` 或 `localhost`。
- Dashboard 由本地 API 在 `/dashboard/` 路径托管，只通过同源 API 读写，不直接解析 runtime 文件。
- API 不发送宽泛 CORS 许可，外部网页不能跨源读取本机配置或模型接口。
- runtime、logs、memory JSONL、career JSONL、growth JSONL 等真实运行数据默认不进入 Git。
- secret-like 内容会被拒绝或 redacted。
- Career 不自动投递，不自动发送外部消息。
- Automation 默认只创建 proposal/preflight，不直接执行高风险动作。
- MCP、LiteLLM、RAG、n8n、LangGraph 与浏览器自动化当前没有启用。

## 8. 故障排查

API 没起来：

```powershell
Get-Content runtime/onepal_api.err.log -Tail 80
```

Dashboard 显示 API error：

```powershell
Invoke-RestMethod http://127.0.0.1:18790/health
```

端口被占用时，先停止 OnePal：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop_onepal.ps1 -Force
```

再重新启动：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_onepal.ps1
```
