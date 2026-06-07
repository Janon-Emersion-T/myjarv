from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.knowledge.loader import knowledge_loader
from app.memory import memory_store


AGILE_PHASES = [
    {"name": "discovery", "status": "planned"},
    {"name": "sprint_1", "status": "planned"},
    {"name": "sprint_2", "status": "planned"},
    {"name": "qa_release", "status": "planned"},
]
WATERFALL_PHASES = [
    {"name": "requirements", "status": "planned"},
    {"name": "design", "status": "planned"},
    {"name": "implementation", "status": "planned"},
    {"name": "qa", "status": "planned"},
    {"name": "release", "status": "planned"},
]
KANBAN_PHASES = [
    {"name": "backlog", "status": "planned"},
    {"name": "in_progress", "status": "planned"},
    {"name": "review", "status": "planned"},
    {"name": "done", "status": "planned"},
]

ROLE_MAP = {
    "website": "Taylor",
    "seo": "Quinn",
    "content": "Avery",
    "finance": "Ledger",
    "backend": "Atlas",
    "project": "Athena",
    "design": "Iris",
}


class ProjectManager:
    DEFAULT_STATE = {
        "projects": [],
        "worklogs": [],
        "reports": [],
    }

    def __init__(self, root_path: str) -> None:
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)
        self.database_path = self.root / "projects.json"
        if not self.database_path.exists():
            self._save(dict(self.DEFAULT_STATE))

    def create_project(
        self,
        *,
        name: str,
        client_name: str,
        category: str,
        methodology: str,
        owner: str,
        summary: str,
        deadline: str | None = None,
        budget: float | None = None,
        goals: list[str] | None = None,
        departments: list[str] | None = None,
    ) -> dict[str, Any]:
        state = self._load()
        now = self._now()
        project_id = str(uuid.uuid4())
        phases = self._phase_template(methodology)
        tasks = self._decompose_tasks(goals or [summary], phases)
        project = {
            "id": project_id,
            "name": name,
            "client_name": client_name,
            "category": category,
            "methodology": methodology,
            "owner": owner,
            "summary": summary,
            "deadline": deadline,
            "budget": budget,
            "goals": goals or [],
            "departments": departments or ["operations"],
            "status": "planned",
            "health_score": 82,
            "risk_score": 28,
            "phases": phases,
            "tasks": tasks,
            "milestones": [],
            "blockers": [],
            "dependencies": [],
            "workload": self._workload(tasks),
            "sprints": self._sprints(methodology, tasks),
            "kanban": self._kanban(tasks),
            "timeline": self._timeline(phases, deadline),
            "budget_tracking": {
                "budget": budget,
                "spent": 0.0,
                "remaining": budget,
            },
            "invoice_status": {
                "project_value": budget,
                "amount_invoiced": 0.0,
                "amount_paid": 0.0,
                "outstanding": budget,
            },
            "playbooks": self._playbooks(summary, category),
            "release_management": {
                "deployment_readiness_score": 72,
                "qa_approval_required": True,
                "client_approval_required": True,
                "production_release_required": category.lower() in {"development", "website", "software"},
            },
            "created_at": now,
            "updated_at": now,
        }
        state["projects"].append(project)
        self._save(state)
        memory_store.create(
            scope="project",
            key=f"project:{project_id}",
            value=f"{name} for {client_name}: {summary}",
            tags=["project", category.lower()],
            source="project_manager",
            task_id=None,
            summary=summary,
            metadata={"client": client_name, "methodology": methodology, "owner": owner},
        )
        return project

    def list_projects(self) -> list[dict[str, Any]]:
        return self._load()["projects"]

    def get_project(self, project_id: str) -> dict[str, Any]:
        return self._find(self._load()["projects"], project_id)

    def add_milestone(self, project_id: str, *, title: str, due_date: str | None = None, owner: str | None = None) -> dict[str, Any]:
        state = self._load()
        project = self._find(state["projects"], project_id)
        project["milestones"].append(
            {
                "id": str(uuid.uuid4()),
                "title": title,
                "due_date": due_date,
                "owner": owner or project["owner"],
                "status": "planned",
                "created_at": self._now(),
            }
        )
        project["updated_at"] = self._now()
        self._save(state)
        return project

    def add_blocker(self, project_id: str, *, title: str, severity: str, owner: str, notes: str | None = None) -> dict[str, Any]:
        state = self._load()
        project = self._find(state["projects"], project_id)
        project["blockers"].append(
            {
                "id": str(uuid.uuid4()),
                "title": title,
                "severity": severity,
                "owner": owner,
                "notes": notes,
                "status": "open",
                "escalated": severity in {"high", "critical"},
                "created_at": self._now(),
            }
        )
        project["risk_score"] = min(100, project["risk_score"] + (20 if severity in {"high", "critical"} else 8))
        project["health_score"] = max(30, project["health_score"] - (12 if severity in {"high", "critical"} else 5))
        project["updated_at"] = self._now()
        self._save(state)
        return project

    def add_worklog(
        self,
        project_id: str,
        *,
        contributor: str,
        hours: float,
        summary: str,
        task_title: str | None = None,
        billable: bool = True,
    ) -> dict[str, Any]:
        state = self._load()
        project = self._find(state["projects"], project_id)
        record = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "contributor": contributor,
            "hours": hours,
            "summary": summary,
            "task_title": task_title,
            "billable": billable,
            "created_at": self._now(),
        }
        state["worklogs"].append(record)
        project["updated_at"] = self._now()
        self._save(state)
        return record

    def add_dependency(self, project_id: str, *, title: str, depends_on: str, type_: str = "task") -> dict[str, Any]:
        state = self._load()
        project = self._find(state["projects"], project_id)
        project["dependencies"].append(
            {
                "id": str(uuid.uuid4()),
                "title": title,
                "depends_on": depends_on,
                "type": type_,
                "created_at": self._now(),
            }
        )
        project["updated_at"] = self._now()
        self._save(state)
        return project

    def generate_report(self, project_id: str, report_type: str) -> dict[str, Any]:
        state = self._load()
        project = self._find(state["projects"], project_id)
        worklogs = [item for item in state["worklogs"] if item["project_id"] == project_id]
        report = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "type": report_type,
            "generated_at": self._now(),
            "summary": self._report_summary(project, report_type, worklogs),
            "metrics": self._project_metrics(project, worklogs),
        }
        state["reports"].append(report)
        self._save(state)
        return report

    def analytics(self) -> dict[str, Any]:
        state = self._load()
        projects = state["projects"]
        worklogs = state["worklogs"]
        return {
            "projects_total": len(projects),
            "status_counts": dict(Counter(item["status"] for item in projects)),
            "category_counts": dict(Counter(item["category"] for item in projects)),
            "methodology_counts": dict(Counter(item["methodology"] for item in projects)),
            "open_blockers": sum(len([blocker for blocker in item["blockers"] if blocker["status"] == "open"]) for item in projects),
            "deadline_risk_projects": sum(1 for item in projects if self._deadline_risk(item)),
            "average_health_score": round(sum(item["health_score"] for item in projects) / len(projects), 2) if projects else 0.0,
            "average_risk_score": round(sum(item["risk_score"] for item in projects) / len(projects), 2) if projects else 0.0,
            "worklog_hours": round(sum(item["hours"] for item in worklogs), 2),
            "burndown": self._burndown(projects),
        }

    def dashboard(self) -> dict[str, Any]:
        projects = self.list_projects()
        return {
            "projects": projects[:12],
            "analytics": self.analytics(),
            "blockers": [
                {"project_id": project["id"], "project_name": project["name"], **blocker}
                for project in projects
                for blocker in project["blockers"][:5]
            ][:20],
            "timeline": [
                {"project_id": project["id"], "project_name": project["name"], "deadline": project["deadline"], "health_score": project["health_score"]}
                for project in projects[:20]
            ],
        }

    def _phase_template(self, methodology: str) -> list[dict[str, Any]]:
        name = methodology.lower()
        if name == "waterfall":
            return [dict(item) for item in WATERFALL_PHASES]
        if name == "kanban":
            return [dict(item) for item in KANBAN_PHASES]
        return [dict(item) for item in AGILE_PHASES]

    def _decompose_tasks(self, goals: list[str], phases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        tasks = []
        for index, goal in enumerate(goals, start=1):
            phase = phases[min(index - 1, len(phases) - 1)]["name"]
            assigned_agent = self._assign_agent(goal)
            tasks.append(
                {
                    "id": str(uuid.uuid4()),
                    "title": goal,
                    "phase": phase,
                    "status": "planned",
                    "assigned_agent": assigned_agent,
                    "backup_agent": "Athena",
                    "priority_score": min(100, 55 + (index * 6)),
                    "dependencies": [],
                }
            )
        return tasks

    def _assign_agent(self, text: str) -> str:
        blob = text.lower()
        for keyword, agent in ROLE_MAP.items():
            if keyword in blob:
                return agent
        return "Athena"

    def _workload(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        return dict(Counter(task["assigned_agent"] for task in tasks))

    def _sprints(self, methodology: str, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if methodology.lower() not in {"agile", "scrum"}:
            return []
        return [
            {"name": "Sprint 1", "tasks": [task["id"] for task in tasks[: max(1, len(tasks) // 2)]], "status": "planned"},
            {"name": "Sprint 2", "tasks": [task["id"] for task in tasks[max(1, len(tasks) // 2) :]], "status": "planned"},
        ]

    def _kanban(self, tasks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        return {
            "backlog": tasks,
            "in_progress": [],
            "review": [],
            "done": [],
        }

    def _timeline(self, phases: list[dict[str, Any]], deadline: str | None) -> list[dict[str, Any]]:
        return [{"phase": phase["name"], "status": phase["status"], "deadline": deadline} for phase in phases]

    def _playbooks(self, summary: str, category: str) -> list[str]:
        query = f"{category} project playbook {summary}"
        return [item["path"] for item in knowledge_loader.retrieve_relevant(query, limit=3)]

    def _project_metrics(self, project: dict[str, Any], worklogs: list[dict[str, Any]]) -> dict[str, Any]:
        hours = round(sum(item["hours"] for item in worklogs), 2)
        return {
            "health_score": project["health_score"],
            "risk_score": project["risk_score"],
            "open_blockers": len([item for item in project["blockers"] if item["status"] == "open"]),
            "milestones_total": len(project["milestones"]),
            "worklog_hours": hours,
            "deadline_risk": self._deadline_risk(project),
        }

    def _report_summary(self, project: dict[str, Any], report_type: str, worklogs: list[dict[str, Any]]) -> str:
        open_blockers = len([item for item in project["blockers"] if item["status"] == "open"])
        if report_type == "daily":
            return f"Daily report for {project['name']}: {len(worklogs)} worklogs captured, {open_blockers} open blockers, next focus is {project['phases'][0]['name']}."
        if report_type == "weekly":
            return f"Weekly report for {project['name']}: health {project['health_score']}, risk {project['risk_score']}, deadline risk {self._deadline_risk(project)}."
        if report_type == "client":
            return f"Client update for {project['client_name']}: progress is tracked across {len(project['phases'])} phases with {len(project['milestones'])} milestones."
        if report_type == "invoice":
            invoice = project["invoice_status"]
            return f"Invoice status for {project['name']}: invoiced {invoice['amount_invoiced']}, paid {invoice['amount_paid']}, outstanding {invoice['outstanding']}."
        return f"Project report for {project['name']}."

    def _deadline_risk(self, project: dict[str, Any]) -> bool:
        if not project["deadline"]:
            return False
        try:
            deadline = datetime.fromisoformat(project["deadline"])
        except ValueError:
            return False
        days = (deadline - datetime.now(UTC)).days
        return days <= 14 or len([item for item in project["blockers"] if item["status"] == "open"]) >= 2

    def _burndown(self, projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chart = []
        for project in projects[:12]:
            total_tasks = max(1, len(project["tasks"]))
            done_tasks = len([task for task in project["tasks"] if task["status"] == "done"])
            chart.append({"project_id": project["id"], "project_name": project["name"], "remaining": total_tasks - done_tasks})
        return chart

    def _find(self, items: list[dict[str, Any]], record_id: str) -> dict[str, Any]:
        for item in items:
            if item["id"] == record_id:
                return item
        raise ValueError(f"Record not found: {record_id}")

    def _load(self) -> dict[str, Any]:
        payload = json.loads(self.database_path.read_text(encoding="utf-8"))
        changed = False
        for key, default in self.DEFAULT_STATE.items():
            if key not in payload:
                payload[key] = list(default)
                changed = True
        if changed:
            self._save(payload)
        return payload

    def _save(self, payload: dict[str, Any]) -> None:
        self.database_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()


project_manager = ProjectManager(settings.PROJECTS_DIR)
