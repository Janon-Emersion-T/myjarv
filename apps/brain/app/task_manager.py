import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.logger import logger


class TaskManager:
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
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message TEXT NOT NULL,
                    intent_category TEXT NOT NULL DEFAULT 'general',
                    preferred_agent TEXT,
                    selected_agent_json TEXT NOT NULL,
                    supporting_agents_json TEXT NOT NULL DEFAULT '[]',
                    requested_action TEXT,
                    priority INTEGER NOT NULL DEFAULT 3,
                    risk_level TEXT NOT NULL,
                    approval_level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    reasoning TEXT NOT NULL
                )
                """
            )
            self._ensure_column(connection, "tasks", "intent_category", "TEXT NOT NULL DEFAULT 'general'")
            self._ensure_column(connection, "tasks", "supporting_agents_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "tasks", "priority", "INTEGER NOT NULL DEFAULT 3")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
                """
            )

    def _ensure_column(self, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def create_task(self, task: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        record = {
            "id": str(uuid.uuid4()),
            "created_at": now,
            "updated_at": now,
            **task,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks (
                    id, created_at, updated_at, message, intent_category, preferred_agent, selected_agent_json,
                    supporting_agents_json, requested_action, priority, risk_level, approval_level, status, metadata_json, reasoning
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record["created_at"],
                    record["updated_at"],
                    record["message"],
                    record["intent_category"],
                    record.get("preferred_agent"),
                    json.dumps(record["selected_agent"]),
                    json.dumps(record.get("supporting_agents", [])),
                    record.get("requested_action"),
                    record["priority"],
                    record["risk_level"],
                    record["approval_level"],
                    record["status"],
                    json.dumps(record.get("metadata", {})),
                    record["reasoning"],
                ),
            )
        logger.log("INFO", "task.created", "Created task record.", {"task_id": record["id"], "status": record["status"]})
        return self.get_task(record["id"])

    def list_tasks(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [self._row_to_task(row) for row in rows]

    def get_task(self, task_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise ValueError(f"Task not found: {task_id}")
        task = self._row_to_task(row)
        task["approvals"] = self.list_approvals(task_id)
        return task

    def _decide(self, task_id: str, decision: str, reviewer: str, notes: str | None) -> dict[str, Any]:
        approval_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()
        updated_at = created_at
        new_status = "approved" if decision == "approved" else "rejected"

        with self._connect() as connection:
            connection.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, updated_at, task_id),
            )
            connection.execute(
                """
                INSERT INTO approvals (id, task_id, decision, reviewer, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (approval_id, task_id, decision, reviewer, notes, created_at),
            )
        logger.log("INFO", f"task.{decision}", f"Task {decision}.", {"task_id": task_id, "reviewer": reviewer})
        return self.get_task(task_id)

    def approve_task(self, task_id: str, reviewer: str, notes: str | None) -> dict[str, Any]:
        return self._decide(task_id, "approved", reviewer, notes)

    def reject_task(self, task_id: str, reviewer: str, notes: str | None) -> dict[str, Any]:
        return self._decide(task_id, "rejected", reviewer, notes)

    def list_approvals(self, task_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM approvals WHERE task_id = ? ORDER BY created_at DESC",
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _row_to_task(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "message": row["message"],
            "intent_category": row["intent_category"],
            "preferred_agent": row["preferred_agent"],
            "selected_agent": json.loads(row["selected_agent_json"]),
            "supporting_agents": json.loads(row["supporting_agents_json"]),
            "requested_action": row["requested_action"],
            "priority": row["priority"],
            "risk_level": row["risk_level"],
            "approval_level": row["approval_level"],
            "status": row["status"],
            "metadata": json.loads(row["metadata_json"]),
            "reasoning": row["reasoning"],
        }


task_manager = TaskManager(settings.DATABASE_PATH)
