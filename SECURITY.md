# SECURITY.md — OnePal

## Service Boundaries
- All local services listen on 127.0.0.1 only. No external network exposure.
- No ports are forwarded or exposed to LAN/WAN.

## Execution Policy
- NEVER execute downloaded scripts (.sh, .bat, .ps1, .exe, .py from untrusted sources).
- NEVER modify system environment variables.
- NEVER read or expose credentials, API keys, tokens, passwords, or cookies.
- NEVER delete files outside the project workspace.

## Network Policy
- External network requests are restricted to allowed domains specified in workflows/permissions.json.
- All network access goes through the permissions model.

## File System Policy
- File writes restricted to the workspace directory.
- System directories are never written to.
- Secret files (*.key, *.token, *.env) are excluded via .gitignore.

## Permission Model
- `allow` — immediately permitted
- `approval` — requires explicit approval via approval queue
- `plan_only` — requires plan confirmation before execution
- `deny` — blocked

## Skill Installation Safety
- Git clone of skill repos requires APPROVAL.
- ONLY markdown files (README.md, SKILL.md, *.md) are copied to skills/installed/.
- NO scripts, binaries, or code files from external repos are executed.

## Memory Safety
- NEVER silently write to memory/store.json.
- All memory additions go through proposals.json → user approval → store.json.
- Credentials and secrets are NEVER stored in memory.

## Advisor Packet Safety
- Exports do NOT include secrets, API keys, tokens, passwords.
- Only project metadata, memory stats, and configuration summaries are exported.
