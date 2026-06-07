#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
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

from app.project_manager import project_manager  # noqa: E402


def main() -> int:
    project = project_manager.create_project(
        name=f"CLI Project {uuid.uuid4().hex[:6]}",
        client_name="CLI Client",
        category="operations",
        methodology="waterfall",
        owner="Athena",
        summary="Validate the project manager CLI workflow.",
        deadline="2026-07-15T00:00:00+00:00",
        budget=150000,
        goals=["Define project scope", "Track blockers", "Prepare client update"],
        departments=["operations", "finance"],
    )
    project_manager.add_milestone(project["id"], title="Scope approval", due_date="2026-06-20T00:00:00+00:00", owner="Athena")
    project_manager.add_blocker(project["id"], title="Awaiting client inputs", severity="medium", owner="Athena", notes="Need final assets.")
    project_manager.add_worklog(project["id"], contributor="Athena", hours=2.0, summary="Prepared kickoff checklist.", task_title="Kickoff")
    reports = {report_type: project_manager.generate_report(project["id"], report_type) for report_type in ("daily", "weekly", "client", "invoice")}
    payload = {
        "project": project_manager.get_project(project["id"]),
        "analytics": project_manager.analytics(),
        "reports": reports,
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
