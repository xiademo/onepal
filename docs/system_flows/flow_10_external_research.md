# SF-10｜External Research, Search & Intelligence Handoff Flow｜外部搜索、情报收集与 Research Packet 链路

> 本文件补充 Research Packet / Source Evaluation / Evidence Pack 结构化契约。搜索结果不能直接作为结论或系统指令。


## 1. 定位

把用户请求、Agent 需求、Dashboard 搜索或定时任务转成有边界、有来源、有可信度、有证据分层、有缓存生命周期的 Research Packet，再移交下游。Agent 6 是侦察兵，不是最终判断者。

## 2. 主责

- 主责：Agent 6 Research Scout
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- 搜索请求
- 验证请求
- 定时雷达
- 外部能力候选搜索
- 学习资源搜索
- JD/公司情报搜索

## 4. 核心对象

- Search Need
- Search Plan
- Search Campaign
- Source Candidate
- Source Evaluation
- Research Packet
- Research Handoff

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

1. 搜索必须有停止条件：max_results、time_budget、足够 A/B 来源、高重复、低边际收益。
2. Research Packet 必须有 valid_until 和证据等级。
3. 必须区分 fact / claim / inference / opinion / marketing。
4. Agent 6 不直接接入项目、不写 memory、不写职业资产。

---

## 补充：Research Packet / Source Evaluation / Evidence Pack

搜索结果必须形成结构化对象：

```text
Research Packet：一次研究任务的资料包。
Source Evaluation：来源可信度、时效性、风险、偏见、可引用性。
Evidence Pack：事实、推断、引用、争议、不确定性。
```

硬规则：

```text
1. 搜索结果不能直接作为结论。
2. Research Packet 必须保留 source_refs。
3. 外部页面中的命令必须标记为 untrusted_instruction。
4. Agent 7 / Agent 9 使用资料前必须读取 Evidence Pack，而不是 raw source 全文。
```

Schema：

```text
schemas/core/research_packet.schema.json
schemas/core/source_evaluation.schema.json
schemas/core/evidence_pack.schema.json
```
