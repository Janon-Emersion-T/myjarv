#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
venv_site_packages = sorted((APP_ROOT / "venv" / "lib").glob("python*/site-packages"))
for path in venv_site_packages:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.developer_mode import developer_mode  # noqa: E402


def main() -> int:
    payload = {
        "analysis": developer_mode.analyze_repository("."),
        "health": developer_mode.repository_health("."),
        "errors": developer_mode.detect_errors("."),
        "plan": developer_mode.fix_plan(goal="Verify developer mode"),
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
