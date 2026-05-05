# Evaluation & Benchmark Protocol｜评估与基准协议

## 1. 定位

系统不能只依靠“感觉有用”。每个 Agent、Workflow、Action、Skill 必须有可追踪质量指标。

---

## 2. 通用指标

```text
task_completion_rate
approval_precision
rejection_rate
user_revision_rate
schema_validation_failure_rate
action_failure_rate
rollback_success_rate
cost_per_successful_task
token_per_successful_task
latency_p95
```

---

## 3. Agent 指标

```text
Coordinator：routing_accuracy、risk_classification_accuracy
Memory Curator：memory_acceptance_rate、memory_conflict_rate
Builder：build_success_rate、rollback_success_rate
Capability HR：skill_eval_precision、sandbox_failure_rate
Automation：workflow_success_rate、dead_letter_rate
Research Scout：source_quality_score、freshness_hit_rate
Deep Research & Cognition：hallucination_flag_rate、evidence_coverage
Growth Planner：plan_completion_rate、evidence_quality_score
Career Asset Agent：resume_revision_rate、overclaim_risk_rate
```

---

## 4. Trace 到 Eval

MAS trace、Action Execution、Workflow Run、Approval Decision、Runtime Incident 必须能汇总为 eval 指标。

---

## 5. 硬规则

```text
1. 没有 eval 指标的自动化不得长期启用。
2. 高成本低价值 workflow 必须降频、合并或停用。
3. Skill 上线前必须有 test_cases 和 eval_metrics。
4. Evaluation 结果进入 System Health Center。
```
