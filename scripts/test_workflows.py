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

from app.workflow_replacement import workflow_replacement_engine  # noqa: E402


def main() -> int:
    workflow = workflow_replacement_engine.create_workflow(
        "project_coordinator",
        client_name="CLI Client",
        context="Coordinate kickoff, blockers, and weekly updates.",
    )
    payload = {
        "workflow": workflow,
        "simulation": workflow_replacement_engine.simulate(workflow["id"]),
        "replay": workflow_replacement_engine.replay(workflow["id"]),
        "analytics": workflow_replacement_engine.analytics(),
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
