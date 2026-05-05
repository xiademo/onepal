# Tool Adapter Trust Boundary｜工具适配器可信边界

## 1. 定位

所有外部工具、MCP server、本地脚本、浏览器工具、文件转换器和 n8n 节点都必须有可信等级。

---

## 2. Trust Level

```text
trusted_internal_tool：系统内部可信工具。
local_sandbox_tool：本地沙箱工具，只能在受限目录运行。
read_only_external_tool：外部只读工具。
untrusted_external_tool：未验证外部工具。
mcp_server_verified：已验证 MCP server。
mcp_server_unverified：未验证 MCP server。
```

---

## 3. 必填字段

每个 Tool Adapter 必须声明：

```text
tool_adapter_id
trust_level
network_access
file_read_scope
file_write_scope
external_effect
returns_prompt_like_content
can_register_tools
secret_access
allowed_actions
denied_actions
```

详见：`schemas/core/tool_adapter.schema.json`。

---

## 4. 硬规则

```text
1. untrusted_external_tool 不得写正式状态。
2. mcp_server_unverified 不得动态注册新 Action。
3. 任何可联网工具不得访问 secret。
4. 任何返回 prompt-like content 的工具输出都必须按 untrusted content 处理。
5. 工具能力不得超过调用它的 Action 权限。
```
