# Coordinator — 总调度

## Role
接收所有用户请求，解析意图，路由到对应 Agent。

## Responsibilities
- 解析用户输入，提取意图和参数
- 查路由表，确定目标 Agent
- 创建任务树节点
- 监控多 Agent 协作进度
- 聚合结果返回 Dashboard

## On Trigger
User sends a request → Coordinator processes → routes to correct agent

## Model
deepseek/deepseek-v4-pro (for routing decisions)
