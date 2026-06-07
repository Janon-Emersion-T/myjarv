from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from app.agent_loader import get_all_agents
from app.collaboration import collaboration_store
from app.logger import logger
from app.memory import memory_store
from app.routing import routing_store
from app.task_manager import task_manager


def _recent_logs(limit: int = 200) -> list[dict[str, Any]]:
    return logger.read_recent(limit=limit)


def _tasks() -> list[dict[str, Any]]:
    return task_manager.list_tasks()


def _approval_queue(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [task for task in tasks if task["status"] == "waiting_approval"]


def _failed_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [task for task in tasks if task["status"] == "failed"]


def get_dashboard_summary() -> dict[str, Any]:
    tasks = _tasks()
    logs = _recent_logs()
    approvals = _approval_queue(tasks)
    failed = _failed_tasks(tasks)
    status_counts = Counter(task["status"] for task in tasks)
    department_counts = Counter(agent.company_department for agent in get_all_agents())
    memory_analytics = memory_store.analytics()
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "health": "ok",
        "agents_total": len(get_all_agents()),
        "tasks_total": len(tasks),
        "tasks_waiting_approval": len(approvals),
        "tasks_failed": len(failed),
        "logs_total": len(logs),
        "error_logs": len([item for item in logs if item["level"] == "ERROR"]),
        "memory_total": memory_analytics["active_records"],
        "status_counts": dict(status_counts),
        "department_counts": dict(department_counts),
        "routing": routing_store.analytics(),
        "collaboration": collaboration_store.analytics(),
        "memory": memory_analytics,
    }


def get_dashboard_errors() -> dict[str, Any]:
    logs = _recent_logs(300)
    tasks = _tasks()
    return {
        "failed_tasks": _failed_tasks(tasks),
        "error_logs": [item for item in logs if item["level"] == "ERROR"],
        "warning_logs": [item for item in logs if item["level"] == "WARNING"],
    }


def get_dashboard_activity() -> dict[str, Any]:
    logs = _recent_logs(120)
    tasks = _tasks()[:12]
    return {
        "logs": logs[:60],
        "tasks": tasks,
        "collaboration_sessions": collaboration_store.list_sessions(limit=20),
        "routing_traces": routing_store.list_traces(limit=20),
    }


def get_dashboard_reports() -> dict[str, Any]:
    tasks = _tasks()
    summary = get_dashboard_summary()
    by_agent = Counter(task["selected_agent"]["name"] for task in tasks)
    by_priority = Counter(str(task["priority"]) for task in tasks)
    by_risk = Counter(task["risk_level"] for task in tasks)
    project_status = Counter((task.get("routing") or {}).get("project_context", "unassigned") for task in tasks)
    return {
        "summary": summary,
        "task_reports": {
            "by_agent": dict(by_agent),
            "by_priority": dict(by_priority),
            "by_risk": dict(by_risk),
            "by_project_context": dict(project_status),
        },
        "collaboration_report": collaboration_store.analytics(),
        "routing_report": routing_store.analytics(),
    }


def get_dashboard_kpis() -> dict[str, Any]:
    tasks = _tasks()
    completed = [task for task in tasks if task["status"] == "completed"]
    approvals = _approval_queue(tasks)
    collaboration = collaboration_store.analytics()
    routing = routing_store.analytics()
    return {
        "delivery_rate": round((len(completed) / len(tasks)) * 100, 2) if tasks else 0,
        "approval_backlog": len(approvals),
        "failed_rate": round((len(_failed_tasks(tasks)) / len(tasks)) * 100, 2) if tasks else 0,
        "avg_collaboration_quality": collaboration.get("average_quality_score", 0),
        "avg_routing_confidence": routing.get("average_confidence", 0),
        "avg_routing_latency_ms": routing.get("average_latency_ms", 0),
    }


def get_dashboard_pipeline() -> dict[str, Any]:
    tasks = _tasks()
    buckets = {
        "lead": [],
        "proposal": [],
        "delivery": [],
        "review": [],
        "completed": [],
    }
    for task in tasks:
        message = task["message"].lower()
        if "lead" in message or "client" in message:
            buckets["lead"].append(task)
        elif "proposal" in message or "quote" in message or "quotation" in message:
            buckets["proposal"].append(task)
        elif task["status"] in {"routed", "approved", "executing"}:
            buckets["delivery"].append(task)
        elif task["status"] in {"waiting_approval", "failed"}:
            buckets["review"].append(task)
        elif task["status"] == "completed":
            buckets["completed"].append(task)
        else:
            buckets["delivery"].append(task)
    return {
        "stages": {key: value[:20] for key, value in buckets.items()},
        "counts": {key: len(value) for key, value in buckets.items()},
    }


def search_dashboard(query: str) -> dict[str, Any]:
    query_text = query.lower()
    agents = [agent.model_dump() for agent in get_all_agents() if query_text in f"{agent.name} {agent.role} {agent.department}".lower()]
    tasks = [task for task in _tasks() if query_text in f"{task['message']} {task['status']} {task['selected_agent']['name']}".lower()]
    memory = memory_store.search(query=query, limit=20, semantic=True)
    logs = [item for item in _recent_logs(150) if query_text in f"{item['event']} {item['message']}".lower()]
    return {"agents": agents[:20], "tasks": tasks[:20], "memory": memory[:20], "logs": logs[:20]}
