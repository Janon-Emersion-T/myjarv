from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agent_loader import get_all_agents
from app.business_automation import business_automation
from app.collaboration import collaboration_store
from app.config import settings
from app.dashboard import get_dashboard_activity, get_dashboard_business, get_dashboard_developer, get_dashboard_projects, get_dashboard_summary
from app.developer_mode import developer_mode
from app.knowledge.loader import knowledge_loader
from app.memory import memory_store
from app.project_manager import project_manager
from app.routing import routing_store
from app.secops import security_engine
from app.self_learning import self_learning_engine
from app.task_manager import task_manager
from app.tools.store import tool_execution_store
from app.voice.store import voice_store
from app.workflow_replacement import workflow_replacement_engine


class JarvisOperatingSystem:
    def __init__(self, root_path: str) -> None:
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)
        self.snapshot_path = self.root / "operating-system.json"

    def dashboard(self) -> dict[str, Any]:
        payload = {
            "generated_at": self._now(),
            "architecture": {
                "mode": "local-first unified operating system",
                "api_gateway": "FastAPI unified brain router",
                "event_bus": "dashboard, approvals, collaboration, voice, learning, and security snapshots",
                "plugin_architecture": ["tool adapters", "memory adapters", "knowledge pipelines", "workflow catalogs"],
                "runtime": ["brain", "desktop", "rust-core", "self-learning", "security", "voice"],
            },
            "modules": self.modules(),
            "assistants": self.assistants(),
            "reports": {
                "daily_ceo": self.report("daily_ceo"),
                "weekly_strategy": self.report("weekly_strategy"),
                "monthly_business": self.report("monthly_business"),
            },
            "recommendations": self.recommendations(),
            "event_bus": self.event_bus(limit=20),
        }
        self.snapshot_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return payload

    def modules(self) -> list[dict[str, Any]]:
        summary = get_dashboard_summary()
        return [
            {"name": "dashboard", "status": "ready", "summary": summary},
            {"name": "memory", "status": "ready", "summary": memory_store.analytics()},
            {"name": "knowledge", "status": "ready", "summary": knowledge_loader.analytics()},
            {"name": "tools", "status": "ready", "summary": tool_execution_store.analytics()},
            {"name": "approvals", "status": "ready", "summary": task_manager.approval_metrics()},
            {"name": "projects", "status": "ready", "summary": project_manager.analytics()},
            {"name": "developer", "status": "ready", "summary": developer_mode.analytics(".")},
            {"name": "business", "status": "ready", "summary": business_automation.analytics()},
            {"name": "workflows", "status": "ready", "summary": workflow_replacement_engine.analytics()},
            {"name": "security", "status": "ready", "summary": security_engine.metrics()},
            {"name": "voice", "status": "ready", "summary": voice_store.analytics()},
            {"name": "learning", "status": "ready", "summary": self_learning_engine.analytics()},
        ]

    def assistants(self) -> list[dict[str, Any]]:
        departments = {
            "developer": ["engineering", "infrastructure", "development"],
            "marketing": ["marketing", "creative", "seo"],
            "finance": ["finance"],
            "legal": ["legal"],
            "hr": ["human_resources", "operations"],
            "client_support": ["support", "sales"],
        }
        agents = [agent.model_dump() for agent in get_all_agents()]
        cards = []
        for name, matches in departments.items():
            available = [agent for agent in agents if any(match in agent["department"].lower() or match in (agent.get("company_department") or "").lower() for match in matches)]
            cards.append(
                {
                    "assistant": name,
                    "status": "ready",
                    "coverage_agents": [agent["name"] for agent in available[:8]],
                    "coverage_total": len(available),
                    "capability_summary": f"{name.replace('_', ' ').title()} assistant is backed by existing agents, dashboards, and operating workflows.",
                }
            )
        return cards

    def recommendations(self) -> list[dict[str, Any]]:
        summary = get_dashboard_summary()
        business = business_automation.analytics()
        projects = project_manager.analytics()
        learning = self_learning_engine.analytics()
        recommendations = []
        if summary["tasks_waiting_approval"] > 0:
            recommendations.append({"priority": "high", "title": "Clear approval backlog", "detail": "There are tasks waiting for approval across the operating system."})
        if projects["deadline_risk_projects"] > 0:
            recommendations.append({"priority": "high", "title": "Escalate deadline-risk projects", "detail": "At least one project is approaching deadline or has blocker density."})
        if business["qualified_leads"] < business["leads_total"]:
            recommendations.append({"priority": "medium", "title": "Nurture open leads", "detail": "Qualified and unqualified leads should move through nurturing and proposal workflows."})
        if learning["pending_updates"] > 0:
            recommendations.append({"priority": "medium", "title": "Review learning updates", "detail": "Pending learning updates are waiting for human review before knowledge application."})
        if not recommendations:
            recommendations.append({"priority": "low", "title": "System stable", "detail": "No urgent recommendations; continue scheduled review and reporting."})
        return recommendations

    def event_bus(self, limit: int = 50) -> dict[str, Any]:
        return {
            "activity": get_dashboard_activity()["logs"][:limit],
            "security": security_engine.list_events(limit=min(limit, 20)),
            "voice": voice_store.list_sessions(limit=min(limit, 10)),
            "collaboration": collaboration_store.list_sessions(limit=min(limit, 10)),
            "tools": tool_execution_store.list(limit=min(limit, 20)),
            "learning": self_learning_engine.list_events(limit=min(limit, 20)),
            "routing": routing_store.list_traces(limit=min(limit, 20)),
        }

    def report(self, report_type: str) -> dict[str, Any]:
        if report_type == "daily_ceo":
            return {
                "id": str(uuid.uuid4()),
                "type": report_type,
                "generated_at": self._now(),
                "headline": "Daily CEO report",
                "summary": get_dashboard_summary(),
                "highlights": [
                    get_dashboard_developer()["health"]["grade"],
                    get_dashboard_business()["analytics"]["qualified_leads"],
                    get_dashboard_projects()["analytics"]["projects_total"],
                    self_learning_engine.analytics()["pending_updates"],
                ],
            }
        if report_type == "weekly_strategy":
            return {
                "id": str(uuid.uuid4()),
                "type": report_type,
                "generated_at": self._now(),
                "headline": "Weekly business strategy report",
                "summary": {
                    "developer": get_dashboard_developer()["analytics"],
                    "business": get_dashboard_business()["analytics"],
                    "projects": get_dashboard_projects()["analytics"],
                    "learning": self_learning_engine.analytics(),
                },
                "recommendations": self.recommendations(),
            }
        return {
            "id": str(uuid.uuid4()),
            "type": report_type,
            "generated_at": self._now(),
            "headline": "Monthly financial and marketing report",
            "summary": {
                "business": business_automation.analytics(),
                "knowledge": knowledge_loader.analytics(),
                "memory": memory_store.analytics(),
                "security": security_engine.compliance_report(),
            },
        }

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()


jarvis_os = JarvisOperatingSystem(settings.OS_DIR)
