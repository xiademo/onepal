# SF-03｜Memory Lifecycle, Context Compression & Knowledge Retention Flow｜记忆生命周期、上下文压缩与长期沉淀链路

> 本文件补充 Memory Poisoning 防线：Memory Candidate 必须记录 origin_type、confidence、requires_user_confirmation、conflict_refs、expiry_policy。


## 1. 定位

管理长期记忆如何产生、审核、写入、复用、压缩、失效和删除，防止 memory 越积越多导致 Token 膨胀。

## 2. 主责

- 主责：Agent 2 Memory Curator
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- 用户长期偏好
- 系统架构决策
- 学习偏好
- 职业偏好
- 跨 Agent 共享摘要
- 上下文压缩请求

## 4. 核心对象

- Memory Candidate
- Memory Entry
- Memory Merge
- Memory Conflict
- Memory Cleanup Log

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

1. Agent 不直接写 memory，必须生成 Memory Candidate。
2. Memory 不保存完整对话、完整文档、完整报告或 secret。
3. 一旦摘要进入 memory，原始长上下文必须降权、归档或只按需展开。
4. knowledge_graph、growth、career 各自是业务 source of truth，Memory 只保存摘要和偏好。
---

## Engineering Object Binding｜工程对象绑定

流程 03 使用 Memory Candidate State Machine：

```text
draft → pending_review → approved / rejected / merged / expired → writing → active / failed → archived / superseded
```

所有 Memory Candidate 必须符合 `schemas/core/memory_candidate.schema.json`。Memory Candidate 不能跳过 approval 直接写入 active。

---

## 补充：Memory Candidate 来源与污染防护

Memory Candidate 必须增加以下字段：

```text
origin_type: user_direct / user_confirmed / agent_inferred / external_source / system_generated
confidence
requires_user_confirmation
conflict_refs
expiry_policy
promotion_reason
```

规则：

```text
1. user_direct / user_confirmed 可进入普通 review。
2. agent_inferred 默认 requires_user_confirmation=true。
3. external_source 默认不得直接写 memory，只能生成待确认候选。
4. 临时情绪、一次性搜索结果、外部网页内容不得直接成为长期偏好。
5. 与已有 memory 冲突时必须进入 conflict review。
```
