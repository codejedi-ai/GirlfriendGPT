"""Tiny test runner.

Sandbox lacks pytest, so we use stdlib only. Discovers ``test_*`` functions
in every ``test_*.py`` module under this package, runs them, prints a
summary. Async test functions are awaited.

When the user's project venv runs pytest, the same ``def test_*()``
functions are picked up unchanged.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import pkgutil
import sys
import traceback
from pathlib import Path


def discover(package: str = "harness.tests") -> list[tuple[str, object]]:
    pkg = importlib.import_module(package)
    found: list[tuple[str, object]] = []
    for mod_info in pkgutil.iter_modules(pkg.__path__, prefix=package + "."):
        if not mod_info.name.rsplit(".", 1)[1].startswith("test_"):
            continue
        mod = importlib.import_module(mod_info.name)
        for name, obj in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("test_") and obj.__module__ == mod.__name__:
                found.append((f"{mod.__name__}::{name}", obj))
    return found


def run(only: str | None = None) -> int:
    tests = discover()
    if only:
        tests = [(n, f) for n, f in tests if only in n]
    passed = 0
    failed: list[tuple[str, str]] = []
    for name, fn in tests:
        try:
            result = fn()
            if inspect.iscoroutine(result):
                asyncio.run(result)
            print(f"  PASS  {name}")
            passed += 1
        except Exception:
            failed.append((name, traceback.format_exc()))
            print(f"  FAIL  {name}")
    print()
    print(f"  {passed} passed, {len(failed)} failed, {len(tests)} total")
    for name, tb in failed:
        print()
        print(f"--- {name} ---")
        print(tb)
    return 0 if not failed else 1


if __name__ == "__main__":
    # Ensure repo root is on sys.path so "harness..." imports work.
    here = Path(__file__).resolve()
    repo_root = here.parents[4]  # harness/tests/_runner.py -> ../../../../
    sys.path.insert(0, str(repo_root))
    only = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(run(only))
