# Skill Package Spec｜Skill 包规格

## 1. 定位

Skill 不是随手保存的 prompt 片段，而是可测试、可禁用、可评估、可升级的能力包。

---

## 2. 必填字段

```text
skill_id
name
version
owner_agent
description
trigger_conditions
input_schema_ref
output_schema_ref
required_actions
permission_required
risk_level
test_cases
eval_metrics
sandbox_status
enabled
deprecated_reason
```

详见：`schemas/core/skill.schema.json`。

---

## 3. 生命周期

```text
draft → sandbox → evaluated → approved / rejected → enabled → deprecated / archived
```

---

## 4. 硬规则

```text
1. Skill 上线前必须有 input_schema_ref 和 output_schema_ref。
2. Skill required_actions 必须全部已注册。
3. Skill 必须经过 sandbox。
4. Skill 必须有 test_cases 和 eval_metrics。
5. Skill 不得绕过 Permission Profile。
```
