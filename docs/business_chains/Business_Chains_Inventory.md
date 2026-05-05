# Business Chains Inventory｜业务链路清单

> 本文件替代旧版 `11_Process_Chains_Inventory.md`。  
> 注意：本文件使用 BC 编号，不再占用 System Flow 的 SF-01~SF-16 编号。

## 1. 定位

Business Chains 描述用户场景中的业务闭环。它们可以调用 System Flows，但不能替代 System Flows。

```text
Business Chain = 用户目标 / 业务场景闭环
System Flow = 系统控制平面 / 工程治理链路
```

---

## 2. BC-01 ~ BC-16

| 编号 | 名称 | 主要调用的 System Flows |
|---|---|---|
| BC-01 | 模糊需求结构化与路由 | SF-01, SF-06 |
| BC-02 | Proposal / Approval 业务审批闭环 | SF-02, SF-06 |
| BC-03 | 记忆捕获与长期偏好沉淀 | SF-03, SF-06 |
| BC-04 | OpenCode 工程实现业务请求 | SF-04, SF-15, SF-16 |
| BC-05 | 外部能力招聘与接入评估 | SF-05, SF-06 |
| BC-06 | 内部 Skill 生成、训练与比武 | SF-05, SF-14 |
| BC-07 | 功能组装与 Feature Assembly | SF-07, SF-04, SF-15 |
| BC-08 | 文档输入与资料转换 | SF-08, SF-06 |
| BC-09 | n8n 定时任务与系统健康检查 | SF-09, SF-14, SF-16 |
| BC-10 | 平台与软件更新检查 | SF-14, SF-15, SF-16 |
| BC-11 | Trend Radar 前沿趋势雷达 | SF-10, SF-11 |
| BC-12 | 主动搜索与情报收集 | SF-10, SF-09 |
| BC-13 | 前沿深度解读 | SF-10, SF-11 |
| BC-14 | 每日认知拓展 | SF-11, SF-12 |
| BC-15 | 目标型成长规划 | SF-12, SF-09 |
| BC-16 | 职业资产 / JD / 简历链路 | SF-13, SF-10, SF-08 |

---

## 3. 规则

```text
1. Business Chain 不直接执行工具，只能请求 Action。
2. Business Chain 不绕过 Permission Profile。
3. Business Chain 中的自动化必须进入 Workflow Registry。
4. Business Chain 涉及服务启动、端口、部署、回滚时必须调用 SF-16。
5. Business Chain 涉及写正式状态时必须调用 SF-06 并写 audit。
```
