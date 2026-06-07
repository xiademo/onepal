#!/usr/bin/env python3
"""Small local pytest-compatible entrypoint for OnePal script tests.

The current OnePal tests are standard-library scripts that report their own
PASS/FAIL counts. This module lets the documented command shape
`py -m pytest tests/test_*.py` run those scripts without installing pytest.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


RESULT_RE = re.compile(r"Results:\s*(\d+)/(\d+)\s+PASS,\s*(\d+)/(\d+)\s+FAIL")
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _collect_targets(args: list[str]) -> list[Path]:
    paths: list[Path] = []
    for arg in args:
        if arg.startswith("-"):
            continue
        p = Path(arg)
        if p.is_dir():
            paths.extend(sorted(p.glob("test_*.py")))
        else:
            paths.append(p)
    if not paths:
        paths.extend(sorted(Path("tests").glob("test_*.py")))
    return paths


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if any(a in ("--version", "-V") for a in args):
        print("pytest compatibility runner for OnePal script tests")
        return 0

    targets = _collect_targets(args)
    if not targets:
        print("no test files found")
        return 5

    total_passed = 0
    total_tests = 0
    failed_files = 0

    for target in targets:
        print(f"\n=== {target} ===")
        if not target.exists():
            print(f"missing test file: {target}")
            failed_files += 1
            continue

        result = subprocess.run(
            [sys.executable, str(target)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
        if result.returncode != 0:
            failed_files += 1

        for match in RESULT_RE.finditer(result.stdout or ""):
            total_passed += int(match.group(1))
            total_tests += int(match.group(2))

    print("\n=== pytest compatibility summary ===")
    if total_tests:
        print(f"Results: {total_passed}/{total_tests} PASS")
    print(f"Files: {len(targets) - failed_files}/{len(targets)} PASS, {failed_files}/{len(targets)} FAIL")
    return 0 if failed_files == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
