# Memory Update Protocol

## Overview
When a task reveals information worth remembering, generate a Memory Update Proposal. Never write directly to memory/store.json without user approval.

## Proposal Categories

| Type | When to Use | Example |
|------|-------------|---------|
| `decision` | Architecture decision, tool choice | "Chose OpenCode + DeepSeek as main system" |
| `preference` | User preference, habit | "User prefers actionable steps first" |
| `pattern` | Recurring behavior | "User likes structured prompts" |
| `feedback` | User correction | "AGENTS.md should be concise" |

## Format
```json
{
  "type": "decision",
  "content": "Decision description",
  "evidence": "What supports this",
  "confidence": 0.0 - 1.0,
  "tags": ["tag1", "tag2"]
}
```

## Safety
- Never store credentials, API keys, company secrets.
- Never write to store.json without approval.
- Always include evidence.
