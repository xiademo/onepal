# SF-05｜Capability Evaluation & Skill Lifecycle Flow｜能力评估与 Skill 生命周期链路

> 本文件替代旧标题中的 External Capability Evaluation & Skill Onboarding。SF-05 统一负责外部能力评估、内部 Skill 生成、Skill Tournament、Sandbox、Registry、淘汰。Feature 产品化发布归 SF-07。


## 1. 定位

判断 GitHub 项目、工具、Skill、MCP、n8n 模板、脚本、API 或框架是否值得纳入系统。搜索由流程 10 完成，本流程负责评估、隔离测试、注册和接入建议。

## 2. 主责

- 主责：Agent 4 Capability HR
- 协作：Coordinator、Task Tree Engine、流程 02 审批、流程 14 健康治理、流程 15 备份回滚、流程 16 Runtime（按需）

## 3. 典型触发

- Research Packet 中的工具候选
- 用户指定 GitHub 项目
- Agent 7 前沿项目启发
- Builder 发现工具需求

## 4. 核心对象

- Capability Candidate
- Capability Evaluation
- Sandbox Test
- Capability Registry Entry
- Onboarding Decision

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

1. 外部能力必须先评估，再 sandbox，再注册。
2. GitHub 热度不等于可接入价值。
3. 需要安装依赖、执行脚本、联网、写文件的能力至少 R2。
4. 高风险能力必须审批。
5. reference_only 不得被 workflow 当作可执行工具。

---

## 补充：Skill Lifecycle 边界

SF-05 统一负责 Skill 生命周期：

```text
skill_candidate → sandbox → evaluated → tournament → approved / rejected → enabled → deprecated / archived
```

Skill 必须使用 `schemas/core/skill.schema.json`。Skill 上线前必须满足：

```text
1. required_actions 全部已注册。
2. input_schema_ref / output_schema_ref 存在。
3. permission_required 明确。
4. risk_level 明确。
5. test_cases 存在。
6. eval_metrics 存在。
7. sandbox_status = passed。
```

Feature 产品化发布归 SF-07，不归 SF-05。
