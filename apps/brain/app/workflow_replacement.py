from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.approval_engine import approval_engine
from app.business_automation import business_automation
from app.browser.planner import browser_planner
from app.config import settings
from app.developer_mode import developer_mode
from app.knowledge.loader import knowledge_loader
from app.memory import memory_store
from app.project_manager import project_manager
from app.tools.registry import tool_registry


WORKFLOW_LIBRARY: dict[str, dict[str, Any]] = {
    "receptionist": {
        "role": "Receptionist",
        "department": "operations",
        "priority": "high",
        "steps": ["Receive inquiry", "Classify request", "Book appointment", "Route to owner", "Log follow-up"],
        "tools": ["calendar_tool", "email_tool", "whatsapp_tool"],
        "channels": ["phone", "email", "whatsapp", "dashboard"],
    },
    "sales_assistant": {
        "role": "Sales Assistant",
        "department": "sales",
        "priority": "high",
        "steps": ["Capture lead", "Qualify lead", "Move pipeline", "Deliver proposal", "Follow up"],
        "tools": ["proposal_generator", "email_tool", "crm_sync"],
        "channels": ["email", "linkedin", "dashboard"],
    },
    "project_coordinator": {
        "role": "Project Coordinator",
        "department": "operations",
        "priority": "high",
        "steps": ["Create project", "Assign work", "Track blockers", "Prepare weekly update", "Escalate risks"],
        "tools": ["project_scanner", "calendar_tool", "documentation_generator"],
        "channels": ["dashboard", "email", "meeting_notes"],
    },
    "junior_developer": {
        "role": "Junior Developer",
        "department": "development",
        "priority": "medium",
        "steps": ["Read repo", "Take implementation slice", "Run tests", "Open change summary", "Escalate uncertainty"],
        "tools": ["project_scanner", "code_generator", "code_reviewer"],
        "channels": ["repo", "cli", "dashboard"],
    },
    "seo_assistant": {
        "role": "SEO Assistant",
        "department": "marketing",
        "priority": "medium",
        "steps": ["Run audit", "Research keywords", "Prepare recommendations", "Track competitor changes", "Report monthly"],
        "tools": ["seo_audit_tool", "browser_search_tool"],
        "channels": ["dashboard", "browser", "docs"],
    },
    "content_writer": {
        "role": "Content Writer",
        "department": "marketing",
        "priority": "medium",
        "steps": ["Draft brief", "Build outline", "Write article", "Review brand voice", "Prepare publishing checklist"],
        "tools": ["documentation_generator", "browser_search_tool"],
        "channels": ["docs", "dashboard"],
    },
    "finance_assistant": {
        "role": "Finance Assistant",
        "department": "finance",
        "priority": "high",
        "steps": ["Track invoices", "Send reminders", "Confirm payments", "Escalate overdue cases", "Prepare status report"],
        "tools": ["email_tool", "calendar_tool"],
        "channels": ["email", "dashboard"],
    },
    "support_assistant": {
        "role": "Support Assistant",
        "department": "support",
        "priority": "high",
        "steps": ["Capture ticket", "Triage severity", "Route to owner", "Send response", "Escalate blocker"],
        "tools": ["documentation_generator", "email_tool", "whatsapp_tool"],
        "channels": ["dashboard", "email", "whatsapp"],
    },
    "documentation_assistant": {
        "role": "Documentation Assistant",
        "department": "operations",
        "priority": "medium",
        "steps": ["Collect facts", "Draft document", "Add SOP format", "Review change log", "Publish update"],
        "tools": ["documentation_generator", "code_reviewer"],
        "channels": ["docs", "repo", "dashboard"],
    },
    "qa_tester": {
        "role": "QA Tester",
        "department": "quality",
        "priority": "high",
        "steps": ["Prepare scenario", "Run regression checks", "Capture defects", "Recommend release status", "Archive evidence"],
        "tools": ["playwright", "selenium", "code_reviewer"],
        "channels": ["browser", "dashboard", "repo"],
    },
}


class WorkflowReplacementEngine:
    DEFAULT_STATE = {"workflows": [], "events": [], "snapshots": []}

    def __init__(self, root_path: str) -> None:
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)
        self.database_path = self.root / "workflow_replacements.json"
        if not self.database_path.exists():
            self._save(dict(self.DEFAULT_STATE))

    def create_workflow(self, workflow_key: str, *, client_name: str | None = None, context: str | None = None) -> dict[str, Any]:
        if workflow_key not in WORKFLOW_LIBRARY:
            raise ValueError(f"Unknown workflow: {workflow_key}")
        state = self._load()
        template = WORKFLOW_LIBRARY[workflow_key]
        workflow_id = str(uuid.uuid4())
        now = self._now()
        task_map = self._task_map(template["steps"], template["department"])
        workflow = {
            "id": workflow_id,
            "workflow_key": workflow_key,
            "role": template["role"],
            "department": template["department"],
            "client_name": client_name,
            "context": context or template["role"],
            "status": "draft",
            "priority": template["priority"],
            "steps": task_map,
            "dependencies": self._dependencies(task_map),
            "tools": self._tool_integration(template["tools"]),
            "knowledge_refs": self._knowledge_refs(template["role"], template["department"]),
            "memory_refs": self._memory_refs(template["role"], client_name),
            "risk_classification": self._risk_classification(template),
            "approval_mapping": self._approval_mapping(template, context or template["role"]),
            "automation_score": self._automation_score(template),
            "confidence_score": self._confidence_score(template),
            "approval_confidence_score": self._approval_confidence_score(template),
            "timeline_analysis": self._timeline_analysis(task_map),
            "kpis": self._kpis(template),
            "sop": self._sop(template, task_map),
            "documentation": self._documentation(template, context or template["role"]),
            "simulation": self._simulation(template, context or template["role"]),
            "replay_ready": True,
            "rollback_ready": True,
            "failure_recovery": self._failure_recovery(template),
            "optimization": self._optimization(template),
            "escalation_chain": self._escalation_chain(template["department"]),
            "human_review_checkpoints": self._human_review_checkpoints(template),
            "approval_integrated": True,
            "dashboard_ready": True,
            "created_at": now,
            "updated_at": now,
        }
        state["workflows"].append(workflow)
        self._event(state, workflow_id, "created", {"workflow_key": workflow_key, "client_name": client_name})
        self._save(state)
        memory_store.create(
            scope="project",
            key=f"workflow:{workflow_id}",
            value=f"{template['role']} replacement workflow for {client_name or 'internal use'}",
            tags=["workflow", workflow_key, template["department"]],
            source="workflow_replacement",
            task_id=None,
            summary=context or template["role"],
            metadata={"workflow_key": workflow_key, "department": template["department"]},
        )
        return workflow

    def list_workflows(self) -> list[dict[str, Any]]:
        return self._load()["workflows"]

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        return self._find(self._load()["workflows"], workflow_id)

    def simulate(self, workflow_id: str) -> dict[str, Any]:
        state = self._load()
        workflow = self._find(state["workflows"], workflow_id)
        payload = {
            "workflow_id": workflow_id,
            "status": "simulation",
            "step_count": len(workflow["steps"]),
            "bottlenecks": self._bottlenecks(workflow),
            "optimization": workflow["optimization"],
            "approval_mapping": workflow["approval_mapping"],
            "timeline_analysis": workflow["timeline_analysis"],
        }
        self._event(state, workflow_id, "simulated", payload)
        self._save(state)
        return payload

    def replay(self, workflow_id: str) -> dict[str, Any]:
        state = self._load()
        workflow = self._find(state["workflows"], workflow_id)
        snapshot = {
            "id": str(uuid.uuid4()),
            "workflow_id": workflow_id,
            "mode": "replay",
            "steps": workflow["steps"],
            "generated_at": self._now(),
        }
        state["snapshots"].append(snapshot)
        self._event(state, workflow_id, "replayed", {"snapshot_id": snapshot["id"]})
        self._save(state)
        return snapshot

    def analytics(self) -> dict[str, Any]:
        state = self._load()
        workflows = state["workflows"]
        return {
            "workflows_total": len(workflows),
            "by_role": dict(Counter(item["role"] for item in workflows)),
            "by_department": dict(Counter(item["department"] for item in workflows)),
            "average_automation_score": round(sum(item["automation_score"] for item in workflows) / len(workflows), 2) if workflows else 0.0,
            "average_confidence_score": round(sum(item["confidence_score"] for item in workflows) / len(workflows), 2) if workflows else 0.0,
            "average_approval_confidence_score": round(sum(item["approval_confidence_score"] for item in workflows) / len(workflows), 2) if workflows else 0.0,
            "events_total": len(state["events"]),
            "snapshots_total": len(state["snapshots"]),
        }

    def dashboard(self) -> dict[str, Any]:
        workflows = self.list_workflows()
        return {
            "workflows": workflows[:12],
            "analytics": self.analytics(),
            "bottlenecks": [{"workflow_id": item["id"], "role": item["role"], "bottlenecks": self._bottlenecks(item)} for item in workflows[:12]],
        }

    def cli_catalog(self) -> dict[str, Any]:
        return {
            "catalog": [
                {
                    "workflow_key": key,
                    "role": value["role"],
                    "department": value["department"],
                    "priority": value["priority"],
                    "steps": value["steps"],
                }
                for key, value in sorted(WORKFLOW_LIBRARY.items())
            ]
        }

    def _task_map(self, steps: list[str], department: str) -> list[dict[str, Any]]:
        return [
            {
                "id": str(uuid.uuid4()),
                "title": step,
                "owner": self._owner_for_step(step, department),
                "status": "planned",
                "sequence": index,
            }
            for index, step in enumerate(steps, start=1)
        ]

    def _owner_for_step(self, step: str, department: str) -> str:
        text = step.lower()
        if "invoice" in text or "payment" in text:
            return "Ledger"
        if "qa" in text or "test" in text:
            return "Quinn"
        if "seo" in text or "keyword" in text:
            return "Neil"
        if "proposal" in text or "lead" in text:
            return "Athena"
        if "document" in text or "changelog" in text:
            return "Docu"
        if department == "development":
            return "Taylor"
        return "Athena"

    def _dependencies(self, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        dependencies = []
        for previous, current in zip(steps, steps[1:]):
            dependencies.append({"from": previous["id"], "to": current["id"], "type": "sequential"})
        return dependencies

    def _tool_integration(self, tool_names: list[str]) -> list[dict[str, Any]]:
        available = {tool["name"]: tool for tool in tool_registry.list_tools()}
        return [
            {
                "name": tool_name,
                "available": tool_name in available,
                "mode": available.get(tool_name, {}).get("mode", "plan") if tool_name in available else "plan",
            }
            for tool_name in tool_names
        ]

    def _knowledge_refs(self, role: str, department: str) -> list[str]:
        return [item["path"] for item in knowledge_loader.retrieve_relevant(f"{role} {department} workflow", limit=4)]

    def _memory_refs(self, role: str, client_name: str | None) -> list[str]:
        query = role if not client_name else f"{role} {client_name}"
        return [item["id"] for item in memory_store.search(query=query, scope=None, semantic=True)[:4]]

    def _risk_classification(self, template: dict[str, Any]) -> dict[str, Any]:
        blob = " ".join(template["steps"]).lower()
        if any(keyword in blob for keyword in ("invoice", "payment", "proposal")):
            level = "HIGH"
        elif any(keyword in blob for keyword in ("qa", "publish", "support", "book")):
            level = "MEDIUM"
        else:
            level = "LOW"
        return {"level": level, "department": template["department"], "priority": template["priority"]}

    def _approval_mapping(self, template: dict[str, Any], context: str) -> dict[str, Any]:
        task = {
            "message": context,
            "requested_action": "workflow replacement",
            "approval_level": self._risk_classification(template)["level"],
            "risk_level": self._risk_classification(template)["level"],
            "metadata": {"approval_department": template["department"]},
        }
        return approval_engine.build_policy(task)

    def _automation_score(self, template: dict[str, Any]) -> float:
        base = 0.65 + (0.05 if len(template["tools"]) >= 2 else 0) + (0.05 if len(template["channels"]) >= 2 else 0)
        if template["priority"] == "high":
            base -= 0.03
        return round(min(0.96, base), 2)

    def _confidence_score(self, template: dict[str, Any]) -> float:
        return round(min(0.95, 0.62 + (len(template["steps"]) * 0.03)), 2)

    def _approval_confidence_score(self, template: dict[str, Any]) -> float:
        return round(min(0.94, 0.58 + (0.1 if template["department"] in {"finance", "operations"} else 0.06)), 2)

    def _timeline_analysis(self, steps: list[dict[str, Any]]) -> dict[str, Any]:
        return {"estimated_minutes": len(steps) * 18, "parallelizable_steps": max(0, len(steps) - 3), "critical_path": steps[:3]}

    def _kpis(self, template: dict[str, Any]) -> list[str]:
        return [
            f"{template['role']} response time",
            f"{template['role']} completion rate",
            f"{template['role']} escalation rate",
        ]

    def _sop(self, template: dict[str, Any], task_map: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "title": f"{template['role']} Replacement SOP",
            "steps": [f"{task['sequence']}. {task['title']} ({task['owner']})" for task in task_map],
        }

    def _documentation(self, template: dict[str, Any], context: str) -> dict[str, Any]:
        return {
            "title": f"{template['role']} Workflow Replacement",
            "summary": context,
            "sections": ["Purpose", "Inputs", "Execution Steps", "Approvals", "Escalations", "Recovery"],
        }

    def _simulation(self, template: dict[str, Any], context: str) -> dict[str, Any]:
        browser_plan = browser_planner.create_plan(f"{template['role']} browser workflow: {context}")
        return {
            "mode": "planning_only",
            "browser_plan": browser_plan,
            "developer_support": developer_mode.fix_plan(goal=f"Support {template['role']} workflow automation", path="."),
        }

    def _failure_recovery(self, template: dict[str, Any]) -> list[str]:
        return [
            "Retry the failed step with preserved context.",
            "Escalate to the department owner if the second attempt fails.",
            "Archive the failed run and attach evidence for review.",
        ]

    def _optimization(self, template: dict[str, Any]) -> list[str]:
        return [
            f"Automate repeatable {template['department']} data capture where safe.",
            "Collapse duplicate handoffs into one structured intake record.",
            "Keep approvals only at externally impactful checkpoints.",
        ]

    def _escalation_chain(self, department: str) -> list[str]:
        if department == "finance":
            return ["Ledger", "Morgan", "Jarvis"]
        if department == "development":
            return ["Taylor", "Tony", "Jarvis"]
        return ["Athena", "Jarvis"]

    def _human_review_checkpoints(self, template: dict[str, Any]) -> list[str]:
        checkpoints = ["Before external communication", "Before financial or legal commitment"]
        if template["department"] == "development":
            checkpoints.append("Before deployment or merge")
        return checkpoints

    def _bottlenecks(self, workflow: dict[str, Any]) -> list[str]:
        items = []
        if workflow["approval_mapping"]["approval_level"] in {"HIGH", "CRITICAL"}:
            items.append("Approval chain may slow completion.")
        if len(workflow["tools"]) <= 1:
            items.append("Low tool coverage increases manual effort.")
        if len(workflow["steps"]) >= 5:
            items.append("Sequential handoffs create coordination drag.")
        return items or ["No immediate bottlenecks detected."]

    def _event(self, state: dict[str, Any], workflow_id: str, event_type: str, payload: dict[str, Any]) -> None:
        state["events"].append(
            {
                "id": str(uuid.uuid4()),
                "workflow_id": workflow_id,
                "event_type": event_type,
                "payload": payload,
                "created_at": self._now(),
            }
        )

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


workflow_replacement_engine = WorkflowReplacementEngine(settings.WORKFLOWS_DIR)
