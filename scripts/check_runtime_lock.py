#!/usr/bin/env python3
"""OnePal Runtime Lock Check - Task 04-A

Checks runtime/runtime_lock.json for system lock status.
Does NOT create or modify the lock file.

Usage:
    py scripts/check_runtime_lock.py
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = PROJECT_ROOT / "runtime" / "runtime_lock.json"


def main():
    if not LOCK_FILE.exists():
        result = {
            "status": "unlocked",
            "file_exists": False,
            "message": "runtime_lock.json not found; system is not locked"
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    try:
        with open(LOCK_FILE, "r", encoding="utf-8") as f:
            lock = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        result = {
            "status": "error",
            "file_exists": True,
            "message": f"runtime_lock.json is invalid JSON: {e}"
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    locked = lock.get("locked", False)
    result = {
        "status": "locked" if locked else "unlocked",
        "file_exists": True,
        "locked": locked,
        "reason": lock.get("reason", ""),
        "created_at": lock.get("created_at", ""),
        "created_by": lock.get("created_by", ""),
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
