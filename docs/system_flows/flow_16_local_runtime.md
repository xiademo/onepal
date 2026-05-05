# SF-16｜Local Runtime, Deployment & Environment Governance Flow｜本地运行环境、部署与启动治理链路

> 本文件补充 Runtime Service 双状态：lifecycle_status 与 enabled_status；服务是否启用与服务是否健康必须分开。


## 1. 定位

通过 Environment Profile、Write Mode、Service Registry、Service Dependency Graph、Runtime Lock、Local Path Contract、Config Drift、Workflow Activation Gate、Smoke Test、Write Audit 和 Safe Mode，保证本地 AI 工作台安全运行、可控更新、失败可回滚。

## 2. 主责

- 主责：Agent 3 Builder + Agent 5 Automation
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- first-run 初始化
- 启动工作台
- 停止工作台
- 部署更新
- 回滚恢复
- 配置漂移
- 服务异常
- 磁盘/模型资源不足

## 4. 核心对象

- Environment Profile
- Write Mode
- Service Registry
- Service Dependency Graph
- Runtime Lock
- Local Path Contract
- Config Drift Report
- Smoke Test
- Runtime Write Audit
- Runtime Incident

## 5. 标准执行骨架

```text
Intake / Request
↓
Classification / Scope
↓
Risk & Policy Check
↓
Owner Agent Handling
↓
Output / State / Handoff
↓
Audit / Health / Review
```

## 6. Dashboard 对应区域

该流程应在对应 Center 中展示：状态、待处理项、最近运行、风险等级、下一步动作、是否需要审批。

## 7. 关键硬规则

1. Task Tree 涉及启动/停止/依赖/端口/workflow/部署/回滚必须调用流程 16。
2. 所有服务必须登记 Service Registry。
3. 启动、停止、部署、回滚、migration 必须使用 Runtime Lock。
4. prod-local 必须通过 smoke test 才能 ready。
5. n8n 启动不等于 workflow 启用，必须通过 Workflow Activation Gate。
6. prod_write 必须写 Runtime Data Write Audit。
---

## Engineering Object Binding｜工程对象绑定

流程 16 使用以下硬对象：

```text
runtime_service.schema.json：服务注册契约
smoke_test.schema.json：启动烟测契约
Runtime Lock：启动 / 停止 / 部署 / 回滚互斥
Write Mode：profile 对应写入权限
Workflow Activation Gate：n8n workflow 启用门槛
```

prod-local ready 前最低 Smoke Test 必须检查：Dashboard、API health、memory index、approval queue、logs、runtime lock、secrets not in Git。

---

## 补充：Runtime Service 双状态

Runtime Service 必须拆分：

```text
lifecycle_status:
registered / starting / healthy / degraded / unhealthy / stopping / stopped / failed

enabled_status:
enabled / disabled
```

含义：

```text
enabled_status：配置层是否允许服务被启动。
lifecycle_status：运行层服务当前健康状态。
```

硬规则：服务可以 disabled 且 stopped，也可以 enabled 但 unhealthy；不得将 enabled/disabled 与 healthy/stopped 混入同一个 status 字段。

Schema：`schemas/core/runtime_service.schema.json`。
