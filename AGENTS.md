# AGENTS.md

## Core Behavior
- Think before editing.
- Prefer small, verifiable changes.
- Do not rewrite unrelated files.
- Do not over-engineer prototypes.

## Safety Rules
- Do not touch OpenCode/ directory.
- Do not read secrets, API keys, tokens, passwords, cookies.
- Do not modify global environment variables without confirmation.
- Do not delete files unless explicitly asked.
- High-risk actions go to approval queue.

## Workflow
- Use Plan mode before Build mode.
- Every important change needs verification steps.
- After changes, explain what changed and how to test.

## Memory
- Memory updates require a proposal first.
- Never silently write to memory/store.json.
- Wait for user approval before committing to long-term memory.

## Skills
- Do not load all skills by default.
- Load only the relevant skill for the current task.

## Token-Saving
- Prefer directory listing at 2 levels max.
- For logs, read only the last 80 lines unless asked otherwise.
