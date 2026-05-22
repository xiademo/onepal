#!/usr/bin/env python3
"""OnePal Write Mode Check - Task 04-A

Checks runtime/write_mode.json for current write mode configuration.
Does NOT create or modify the write mode file.

Modes: local_dry_run (default) | local_write_with_approval | safe_readonly | locked

Usage:
    py scripts/check_write_mode.py
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODE_FILE = PROJECT_ROOT / "runtime" / "write_mode.json"

VALID_MODES = {"local_dry_run", "local_write_with_approval", "safe_readonly", "locked"}


def main():
    if not MODE_FILE.exists():
        result = {
            "mode": "local_dry_run",
            "file_exists": False,
            "default": True,
            "message": "write_mode.json not found; defaulting to local_dry_run"
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    try:
        with open(MODE_FILE, "r", encoding="utf-8") as f:
            mode_data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        result = {
            "mode": "local_dry_run",
            "file_exists": True,
            "default": True,
            "message": f"write_mode.json is invalid JSON: {e}; falling back to local_dry_run"
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    mode = mode_data.get("mode", "local_dry_run")
    if mode not in VALID_MODES:
        mode = "local_dry_run"

    result = {
        "mode": mode,
        "file_exists": True,
        "default": False,
        "configured_at": mode_data.get("configured_at", ""),
        "configured_by": mode_data.get("configured_by", ""),
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
