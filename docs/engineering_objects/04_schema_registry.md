# Schema Registry｜核心对象 JSON Schema 注册表

## 1. 定位

Schema Registry 是所有核心工程对象的数据契约中心。

所有核心对象必须有 JSON Schema，避免 Agent、workflow、Dashboard、n8n、脚本之间字段漂移。

---

## 2. 必须注册的核心 Schema

```text
schemas/core/action.schema.json
schemas/core/action_execution.schema.json
schemas/core/agent.schema.json
schemas/core/approval_decision.schema.json
schemas/core/document_packet.schema.json
schemas/core/evidence_pack.schema.json
schemas/core/handoff.schema.json
schemas/core/memory_candidate.schema.json
schemas/core/permission_profile.schema.json
schemas/core/proposal.schema.json
schemas/core/research_packet.schema.json
schemas/core/runtime_service.schema.json
schemas/core/skill.schema.json
schemas/core/smoke_test.schema.json
schemas/core/source_evaluation.schema.json
schemas/core/state_transition.schema.json
schemas/core/subtask_request.schema.json
schemas/core/task.schema.json
schemas/core/task_tree.schema.json
schemas/core/tool_adapter.schema.json
schemas/core/workflow.schema.json
schemas/core/workflow_run.schema.json
```

---

## 3. Schema 变更规则

```text
R1：新增非必填字段，可直接版本化。
R2：新增必填字段、修改 enum、修改对象结构，必须 checkpoint + validation。
R3：破坏兼容性、迁移旧数据、修改核心状态机字段，必须审批 + migration plan + restore test。
```

硬规则：

```text
1. schema 变更必须走 SF-15。
2. R3 schema 变更必须有 migration plan。
3. 核心对象写入前必须 schema validation。
4. 不允许写入 unknown critical fields。
5. Dashboard 表单必须从 Schema Registry 读取字段定义。
```

---

## 4. Packet / Evidence 对象

Document Packet、Research Packet、Source Evaluation、Evidence Pack 是 SF-08 / SF-10 / SF-11 / SF-13 的基础对象，必须结构化，不能只用自然语言资料包传递。

```text
Document Packet：外部文件转换后的可信边界对象。
Research Packet：外部搜索/研究结果对象。
Source Evaluation：来源可信度、时效性、风险标记。
Evidence Pack：事实、推断、引用、争议、不确定性集合。
```
