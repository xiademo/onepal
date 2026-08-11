# OnePal

OnePal is a local-first AI Workbench.

## Quick Start

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_onepal.ps1
```

This runs the startup smoke test, starts the local API at `http://127.0.0.1:18790`,
and opens `dashboard/index.html`.

If `py.exe` cannot find Python, the launcher will try the bundled Codex Python.
You can also pass `-Python <path-to-python.exe>`.

Stop the local API:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop_onepal.ps1
```

User manual:

- docs/user_manual.md

Current architecture source of truth:

- docs/freeze/AI_Workbench_Architecture_Freeze_v0.1.1-final.md

Archived reference docs are stored under:

- docs/archived_reference/

Do not use archived reference files as implementation source of truth.
