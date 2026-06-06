import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.logger import logger


class CollaborationStore:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS collaboration_sessions (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    coordinator TEXT NOT NULL,
                    primary_agent TEXT NOT NULL,
                    participants_json TEXT NOT NULL,
                    reviewers_json TEXT NOT NULL,
                    fallback_agents_json TEXT NOT NULL,
                    approval_required TEXT NOT NULL,
                    status TEXT NOT NULL,
                    shared_workspace_json TEXT NOT NULL,
                    analytics_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS collaboration_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    related_stage TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS collaboration_events (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS collaboration_contributions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    role TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    deliverables_json TEXT NOT NULL,
                    quality_score INTEGER NOT NULL,
                    references_json TEXT NOT NULL,
                    fallback_used TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create_session(self, payload: dict[str, Any]) -> str:
        session_id = payload["id"]
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO collaboration_sessions (
                    id, task_id, mode, strategy, coordinator, primary_agent, participants_json, reviewers_json,
                    fallback_agents_json, approval_required, status, shared_workspace_json, analytics_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    payload["task_id"],
                    payload["mode"],
                    payload["strategy"],
                    payload["coordinator"],
                    payload["primary_agent"],
                    json.dumps(payload.get("participants", [])),
                    json.dumps(payload.get("reviewers", [])),
                    json.dumps(payload.get("fallback_agents", [])),
                    payload["approval_required"],
                    payload["status"],
                    json.dumps(payload.get("shared_workspace", {})),
                    json.dumps(payload.get("analytics", {})),
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )
        return session_id

    def update_session(self, session_id: str, *, status: str | None = None, analytics: dict[str, Any] | None = None, shared_workspace: dict[str, Any] | None = None) -> None:
        now = datetime.now(UTC).isoformat()
        current = self.get_session(session_id)
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE collaboration_sessions
                SET status = ?, analytics_json = ?, shared_workspace_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    status or current["status"],
                    json.dumps(analytics or current["analytics"]),
                    json.dumps(shared_workspace or current["shared_workspace"]),
                    now,
                    session_id,
                ),
            )

    def add_message(self, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO collaboration_messages (
                    id, session_id, task_id, sender, recipient, kind, content, related_stage, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload["session_id"],
                    payload["task_id"],
                    payload["sender"],
                    payload["recipient"],
                    payload["kind"],
                    payload["content"],
                    payload.get("related_stage"),
                    payload["created_at"],
                ),
            )

    def add_event(self, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO collaboration_events (
                    id, session_id, task_id, event_type, actor, stage, message, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload["session_id"],
                    payload["task_id"],
                    payload["event_type"],
                    payload["actor"],
                    payload["stage"],
                    payload["message"],
                    json.dumps(payload.get("payload", {})),
                    payload["created_at"],
                ),
            )

    def add_contribution(self, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO collaboration_contributions (
                    id, session_id, task_id, agent, role, stage, status, summary, deliverables_json,
                    quality_score, references_json, fallback_used, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload["session_id"],
                    payload["task_id"],
                    payload["agent"],
                    payload["role"],
                    payload["stage"],
                    payload["status"],
                    payload["summary"],
                    json.dumps(payload.get("deliverables", [])),
                    payload["quality_score"],
                    json.dumps(payload.get("references", [])),
                    payload.get("fallback_used"),
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )

    def list_sessions(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM collaboration_sessions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_session(row) for row in rows]

    def get_session(self, session_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM collaboration_sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise ValueError(f"Collaboration session not found: {session_id}")
        session = self._row_to_session(row)
        session["messages"] = self.list_messages(session_id)
        session["events"] = self.list_events(session_id)
        session["contributions"] = self.list_contributions(session_id)
        return session

    def get_latest_session_for_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM collaboration_sessions WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
                (task_id,),
            ).fetchone()
        return None if row is None else self.get_session(row["id"])

    def list_messages(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM collaboration_messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_events(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM collaboration_events WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "task_id": row["task_id"],
                "event_type": row["event_type"],
                "actor": row["actor"],
                "stage": row["stage"],
                "message": row["message"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def list_contributions(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM collaboration_contributions WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "task_id": row["task_id"],
                "agent": row["agent"],
                "role": row["role"],
                "stage": row["stage"],
                "status": row["status"],
                "summary": row["summary"],
                "deliverables": json.loads(row["deliverables_json"]),
                "quality_score": row["quality_score"],
                "references": json.loads(row["references_json"]),
                "fallback_used": row["fallback_used"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def analytics(self) -> dict[str, Any]:
        sessions = self.list_sessions(limit=500)
        if not sessions:
            return {
                "total_sessions": 0,
                "average_participants": 0,
                "average_quality_score": 0,
                "by_strategy": {},
                "by_status": {},
                "top_agents": {},
            }
        by_strategy: dict[str, int] = {}
        by_status: dict[str, int] = {}
        top_agents: dict[str, int] = {}
        total_participants = 0
        total_scores = 0
        score_count = 0
        for session in sessions:
            by_strategy[session["strategy"]] = by_strategy.get(session["strategy"], 0) + 1
            by_status[session["status"]] = by_status.get(session["status"], 0) + 1
            total_participants += len(session["participants"])
            for contribution in session.get("contributions", []):
                top_agents[contribution["agent"]] = top_agents.get(contribution["agent"], 0) + 1
                total_scores += contribution["quality_score"]
                score_count += 1
        return {
            "total_sessions": len(sessions),
            "average_participants": round(total_participants / len(sessions), 2),
            "average_quality_score": round(total_scores / score_count, 2) if score_count else 0,
            "by_strategy": by_strategy,
            "by_status": by_status,
            "top_agents": dict(sorted(top_agents.items(), key=lambda item: item[1], reverse=True)[:10]),
        }

    def _row_to_session(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "task_id": row["task_id"],
            "mode": row["mode"],
            "strategy": row["strategy"],
            "coordinator": row["coordinator"],
            "primary_agent": row["primary_agent"],
            "participants": json.loads(row["participants_json"]),
            "reviewers": json.loads(row["reviewers_json"]),
            "fallback_agents": json.loads(row["fallback_agents_json"]),
            "approval_required": row["approval_required"],
            "status": row["status"],
            "shared_workspace": json.loads(row["shared_workspace_json"]),
            "analytics": json.loads(row["analytics_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def next_id(self) -> str:
        return str(uuid.uuid4())

    def now(self) -> str:
        return datetime.now(UTC).isoformat()


collaboration_store = CollaborationStore(settings.DATABASE_PATH)
