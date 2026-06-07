#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
venv_site_packages = sorted((APP_ROOT / "venv" / "lib").glob("python*/site-packages"))
for path in venv_site_packages:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.tools.engine import tool_execution_engine  # noqa: E402
from app.tools.store import tool_execution_store  # noqa: E402


def main() -> int:
    started = time.perf_counter()
    samples = [
        ("file_read", {"path": "README.md"}, False),
        ("git_status", {"path": "."}, False),
        ("safe_shell_plan", {"goal": "Inspect repository"}, True),
        ("project_scanner", {"path": "."}, False),
    ]
    results = []
    for _ in range(8):
        for tool_name, payload, approved in samples:
            results.append(tool_execution_engine.execute(tool_name=tool_name, input_payload=payload, actor="test_tools", approved=approved))
    elapsed = round(time.perf_counter() - started, 3)
    print(
        json.dumps(
            {
                "elapsed_seconds": elapsed,
                "executions": len(results),
                "analytics": tool_execution_store.analytics(),
                "health": tool_execution_store.health(),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
