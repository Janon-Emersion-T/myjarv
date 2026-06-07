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

from app.knowledge.loader import knowledge_loader  # noqa: E402


def main() -> int:
    started = time.perf_counter()
    knowledge_loader.reindex()
    queries = [
        "react dashboard routing",
        "docker deployment health checks",
        "proposal scope pricing",
        "ocr extraction confidence",
        "sri lankan contract guidance",
        "wordpress woocommerce handoff",
    ]
    counts = []
    for _ in range(10):
        for query in queries:
            counts.append(len(knowledge_loader.search(query=query, limit=6, semantic=True)))
    elapsed = round(time.perf_counter() - started, 3)
    print(
        json.dumps(
            {
                "elapsed_seconds": elapsed,
                "queries": len(counts),
                "average_results": round(sum(counts) / len(counts), 2) if counts else 0,
                "analytics": knowledge_loader.analytics(),
                "validation": knowledge_loader.validate(),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
