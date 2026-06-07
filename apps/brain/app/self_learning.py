from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.business_automation import business_automation
from app.config import settings
from app.developer_mode import developer_mode
from app.knowledge.loader import knowledge_loader
from app.logger import logger
from app.memory import memory_store
from app.project_manager import project_manager
from app.secops import security_engine
from app.task_manager import task_manager


class SelfLearningEngine:
    DEFAULT_STATE = {
        "runs": [],
        "events": [],
        "lessons": [],
        "updates": [],
        "playbooks": [],
    }

    def __init__(self, root_path: str) -> None:
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "self_learning.json"
        self.versions_dir = self.root / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.applied_dir = Path(settings.KNOWLEDGE_DIR) / "company" / "self-learning"
        self.applied_dir.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self._save(dict(self.DEFAULT_STATE))

    def run(self, *, limit: int = 100, reviewer: str = "Jarvis", mode: str = "safe") -> dict[str, Any]:
        state = self._load()
        tasks = task_manager.list_tasks()[:limit]
        recent_logs = logger.read_recent(limit=limit * 2)
        timestamp = self._now()

        new_events = self._build_events(tasks, recent_logs)
        for event in new_events:
            if not self._exists(state["events"], event["fingerprint"]):
                state["events"].append(event)

        lessons = self._build_lessons(state["events"], tasks, recent_logs)
        for lesson in lessons:
            if not self._exists(state["lessons"], lesson["fingerprint"]):
                state["lessons"].append(lesson)
                memory_store.create(
                    scope="mistake" if lesson["kind"] == "failure_pattern" else "success_pattern",
                    key=f"lesson:{lesson['id']}",
                    value=lesson["summary"],
                    tags=["self-learning", lesson["kind"], *lesson["tags"]],
                    source="self_learning",
                    task_id=lesson.get("task_id"),
                    summary=lesson["summary"],
                    metadata={"review_state": lesson["review_state"], "source_count": len(lesson["sources"])},
                )

        playbooks = self._build_playbooks(tasks, state["lessons"])
        for playbook in playbooks:
            if not self._exists(state["playbooks"], playbook["fingerprint"]):
                state["playbooks"].append(playbook)

        updates = self._build_updates(state["lessons"], state["playbooks"])
        for update in updates:
            if not self._exists(state["updates"], update["fingerprint"]):
                state["updates"].append(update)

        run = {
            "id": str(uuid.uuid4()),
            "mode": mode,
            "reviewer": reviewer,
            "limit": limit,
            "created_at": timestamp,
            "events_added": len(new_events),
            "lessons_added": len(lessons),
            "playbooks_added": len(playbooks),
            "updates_open": len([item for item in state["updates"] if item["review_state"] == "pending"]),
            "analytics": self._analytics(state),
        }
        state["runs"].append(run)
        self._save(state)
        logger.log("INFO", "learning.run", "Completed self-learning pass.", {"run_id": run["id"], "mode": mode})
        return run

    def dashboard(self) -> dict[str, Any]:
        state = self._load()
        return {
            "analytics": self._analytics(state),
            "runs": list(reversed(state["runs"]))[:10],
            "recent_events": list(reversed(state["events"]))[:20],
            "lessons": list(reversed(state["lessons"]))[:12],
            "pending_updates": [item for item in reversed(state["updates"]) if item["review_state"] == "pending"][:12],
            "playbooks": list(reversed(state["playbooks"]))[:12],
            "trusted_sources": ["internal", "developer_mode", "project_manager", "business_automation", "security_engine"],
            "safety": {
                "review_required_before_apply": True,
                "rollback_supported": True,
                "knowledge_reindex_required_after_apply": True,
            },
        }

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(reversed(self._load()["events"]))[:limit]

    def list_lessons(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(reversed(self._load()["lessons"]))[:limit]

    def list_updates(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(reversed(self._load()["updates"]))[:limit]

    def list_playbooks(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(reversed(self._load()["playbooks"]))[:limit]

    def review_update(self, update_id: str, *, reviewer: str, decision: str, notes: str | None = None) -> dict[str, Any]:
        state = self._load()
        update = self._find(state["updates"], update_id)
        update["review_state"] = decision
        update["reviewed_by"] = reviewer
        update["reviewed_at"] = self._now()
        update["review_notes"] = notes
        self._save(state)
        logger.log("INFO", "learning.review", "Reviewed learning update.", {"update_id": update_id, "decision": decision})
        return update

    def apply_update(self, update_id: str, *, reviewer: str, notes: str | None = None) -> dict[str, Any]:
        state = self._load()
        update = self._find(state["updates"], update_id)
        if update["review_state"] != "approved":
            raise ValueError("Learning update must be approved before applying.")
        slug = self._slugify(update["title"])
        knowledge_path = self.applied_dir / f"{slug}.md"
        previous = knowledge_path.read_text(encoding="utf-8") if knowledge_path.exists() else ""
        rendered = self._render_update(update, reviewer, notes)
        knowledge_path.write_text(rendered, encoding="utf-8")
        version = {
            "id": str(uuid.uuid4()),
            "update_id": update_id,
            "path": str(knowledge_path.relative_to(Path(settings.KNOWLEDGE_DIR))),
            "applied_by": reviewer,
            "notes": notes,
            "applied_at": self._now(),
            "before": previous,
            "after": rendered,
            "semantic_diff": self._semantic_diff(previous, rendered),
        }
        (self.versions_dir / f"{update_id}-{version['id']}.json").write_text(json.dumps(version, ensure_ascii=True, indent=2), encoding="utf-8")
        update["review_state"] = "applied"
        update["applied_by"] = reviewer
        update["applied_at"] = version["applied_at"]
        update["applied_path"] = version["path"]
        self._save(state)
        knowledge_loader.reindex()
        logger.log("INFO", "learning.apply", "Applied learning update.", {"update_id": update_id, "path": version["path"]})
        return {"update": update, "version": version}

    def analytics(self) -> dict[str, Any]:
        return self._analytics(self._load())

    def _build_events(self, tasks: list[dict[str, Any]], recent_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        events = []
        for task in tasks:
            if task["status"] not in {"completed", "failed", "rejected", "blocked"}:
                continue
            outcome = "success" if task["status"] == "completed" else "failure"
            fingerprint = f"task:{task['id']}:{task['status']}"
            events.append(
                {
                    "id": str(uuid.uuid4()),
                    "fingerprint": fingerprint,
                    "kind": "task_outcome",
                    "outcome": outcome,
                    "task_id": task["id"],
                    "intent_category": task.get("intent_category", "general"),
                    "selected_agent": task["selected_agent"]["name"],
                    "status": task["status"],
                    "summary": task["message"],
                    "created_at": self._now(),
                }
            )
        for log in recent_logs:
            if log["level"] != "ERROR":
                continue
            fingerprint = f"log:{log['event']}:{log['message']}"
            events.append(
                {
                    "id": str(uuid.uuid4()),
                    "fingerprint": fingerprint,
                    "kind": "error_signal",
                    "outcome": "failure",
                    "task_id": None,
                    "intent_category": "general",
                    "selected_agent": "Jarvis",
                    "status": "error",
                    "summary": f"{log['event']}: {log['message']}",
                    "created_at": self._now(),
                }
            )
        return events

    def _build_lessons(self, events: list[dict[str, Any]], tasks: list[dict[str, Any]], recent_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        lessons = []
        failed = [item for item in events if item["outcome"] == "failure"]
        success = [item for item in events if item["outcome"] == "success"]
        error_counts = Counter(log["event"] for log in recent_logs if log["level"] == "ERROR")
        for item in failed[:12]:
            lessons.append(
                {
                    "id": str(uuid.uuid4()),
                    "fingerprint": f"lesson:{item['fingerprint']}",
                    "kind": "failure_pattern",
                    "task_id": item["task_id"],
                    "summary": f"Failure pattern detected around {item['summary']}. Add approval-aware guardrails, better reproduction notes, and fallback routing.",
                    "tags": [item["intent_category"], "failure"],
                    "review_state": "pending",
                    "sources": [item["fingerprint"]],
                    "created_at": self._now(),
                }
            )
        for item in success[:12]:
            lessons.append(
                {
                    "id": str(uuid.uuid4()),
                    "fingerprint": f"lesson:{item['fingerprint']}",
                    "kind": "success_pattern",
                    "task_id": item["task_id"],
                    "summary": f"Success pattern captured for {item['summary']}. Reuse the routing, collaboration, and review sequence as a playbook candidate.",
                    "tags": [item["intent_category"], "success"],
                    "review_state": "pending",
                    "sources": [item["fingerprint"]],
                    "created_at": self._now(),
                }
            )
        for event_name, count in error_counts.items():
            if count < 2:
                continue
            lessons.append(
                {
                    "id": str(uuid.uuid4()),
                    "fingerprint": f"lesson:error:{event_name}",
                    "kind": "repeated_error",
                    "task_id": None,
                    "summary": f"Repeated error detected for {event_name} ({count} occurrences). Root-cause review and defensive documentation should be updated.",
                    "tags": ["repeated-error", event_name],
                    "review_state": "pending",
                    "sources": [event_name],
                    "created_at": self._now(),
                }
            )
        return lessons

    def _build_playbooks(self, tasks: list[dict[str, Any]], lessons: list[dict[str, Any]]) -> list[dict[str, Any]]:
        playbooks = []
        grouped: dict[str, list[dict[str, Any]]] = {}
        for task in tasks:
            if task["status"] != "completed":
                continue
            grouped.setdefault(task.get("intent_category", "general"), []).append(task)
        for intent, items in grouped.items():
            agents = sorted({item["selected_agent"]["name"] for item in items})
            matched_lessons = [lesson["summary"] for lesson in lessons if intent in lesson["tags"]][:4]
            playbooks.append(
                {
                    "id": str(uuid.uuid4()),
                    "fingerprint": f"playbook:{intent}",
                    "intent_category": intent,
                    "title": f"{intent.title()} operating playbook",
                    "agents": agents,
                    "steps": [
                        "Review prior routing and approval context.",
                        "Reuse the strongest successful task decomposition.",
                        "Escalate early when confidence, risk, or blockers shift.",
                        "Write memory and knowledge updates after delivery.",
                    ],
                    "lessons": matched_lessons,
                    "created_at": self._now(),
                }
            )
        return playbooks

    def _build_updates(self, lessons: list[dict[str, Any]], playbooks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        updates = []
        for lesson in lessons[:20]:
            updates.append(
                {
                    "id": str(uuid.uuid4()),
                    "fingerprint": f"update:{lesson['fingerprint']}",
                    "title": f"Learning update for {lesson['kind']}",
                    "target_path": "company/self-learning",
                    "review_state": "pending",
                    "content": lesson["summary"],
                    "tags": lesson["tags"],
                    "created_at": self._now(),
                }
            )
        for playbook in playbooks[:10]:
            updates.append(
                {
                    "id": str(uuid.uuid4()),
                    "fingerprint": f"update:{playbook['fingerprint']}",
                    "title": playbook["title"],
                    "target_path": "operations/playbooks",
                    "review_state": "pending",
                    "content": "\n".join(playbook["steps"]),
                    "tags": [playbook["intent_category"], "playbook"],
                    "created_at": self._now(),
                }
            )
        return updates

    def _analytics(self, state: dict[str, Any]) -> dict[str, Any]:
        lessons = state["lessons"]
        updates = state["updates"]
        playbooks = state["playbooks"]
        return {
            "runs_total": len(state["runs"]),
            "events_total": len(state["events"]),
            "lessons_total": len(lessons),
            "updates_total": len(updates),
            "pending_updates": len([item for item in updates if item["review_state"] == "pending"]),
            "applied_updates": len([item for item in updates if item["review_state"] == "applied"]),
            "playbooks_total": len(playbooks),
            "lesson_kinds": dict(Counter(item["kind"] for item in lessons)),
            "coverage": {
                "developer": developer_mode.analytics("."),
                "business": business_automation.analytics(),
                "projects": project_manager.analytics(),
                "security": security_engine.metrics(),
                "knowledge": knowledge_loader.analytics(),
            },
        }

    def _render_update(self, update: dict[str, Any], reviewer: str, notes: str | None) -> str:
        tags = ", ".join(update["tags"])
        return "\n".join(
            [
                "---",
                f"title: {update['title']}",
                'sources: ["internal"]',
                "trusted: true",
                "verified: true",
                "approval_status: approved",
                f"summary: {update['content']}",
                f"tags: [{tags}]",
                f"last_reviewed: {datetime.now(UTC).date().isoformat()}",
                "---",
                "",
                f"# {update['title']}",
                "",
                update["content"],
                "",
                f"Reviewed by {reviewer}.",
                notes or "Applied through the self-learning review pipeline.",
                "",
            ]
        )

    def _semantic_diff(self, before: str, after: str) -> dict[str, Any]:
        before_lines = [line.strip() for line in before.splitlines() if line.strip()]
        after_lines = [line.strip() for line in after.splitlines() if line.strip()]
        return {
            "before_lines": len(before_lines),
            "after_lines": len(after_lines),
            "added_lines": max(0, len(after_lines) - len(before_lines)),
            "changed": before != after,
        }

    def _exists(self, items: list[dict[str, Any]], fingerprint: str) -> bool:
        return any(item["fingerprint"] == fingerprint for item in items)

    def _find(self, items: list[dict[str, Any]], record_id: str) -> dict[str, Any]:
        for item in items:
            if item["id"] == record_id:
                return item
        raise ValueError(f"Record not found: {record_id}")

    def _slugify(self, text: str) -> str:
        cleaned = "".join(char.lower() if char.isalnum() else "-" for char in text).strip("-")
        while "--" in cleaned:
            cleaned = cleaned.replace("--", "-")
        return cleaned[:64] or "learning-update"

    def _load(self) -> dict[str, Any]:
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        changed = False
        for key, default in self.DEFAULT_STATE.items():
            if key not in payload:
                payload[key] = list(default)
                changed = True
        if changed:
            self._save(payload)
        return payload

    def _save(self, payload: dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()


self_learning_engine = SelfLearningEngine(settings.LEARNING_DIR)
