#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
venv_site_packages = sorted((APP_ROOT / "venv" / "lib").glob("python*/site-packages"))
for path in venv_site_packages:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.memory import memory_store  # noqa: E402


def main() -> int:
    started = time.perf_counter()
    batch = []
    marker = uuid.uuid4().hex[:8]
    for index in range(30):
        batch.append(
            {
                "scope": "short_term" if index % 2 == 0 else "long_term",
                "key": f"stress-{marker}-{index}",
                "value": f"Memory stress payload {index} for search, retrieval, and analytics validation.",
                "tags": ["stress", marker, "phase7"],
                "source": "scripts.test_memory",
            }
        )
    imported = memory_store.import_records(batch, merge=True)
    search = memory_store.search(query=marker, limit=10, semantic=True)
    analytics = memory_store.analytics()
    elapsed = round(time.perf_counter() - started, 3)
    print(
        json.dumps(
            {
                "elapsed_seconds": elapsed,
                "imported": imported,
                "search_results": len(search),
                "analytics": analytics,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
