from __future__ import annotations

import json
import sqlite3
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.logger import logger


class ToolExecutionStore:
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
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    agent_name TEXT,
                    task_id TEXT,
                    status TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    approval_requirement TEXT NOT NULL,
                    async_mode INTEGER NOT NULL DEFAULT 0,
                    queued INTEGER NOT NULL DEFAULT 0,
                    input_json TEXT NOT NULL,
                    output_json TEXT,
                    error TEXT,
                    duration_ms REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def record(
        self,
        *,
        tool_name: str,
        actor: str,
        agent_name: str | None,
        task_id: str | None,
        status: str,
        mode: str,
        risk_level: str,
        approval_requirement: str,
        async_mode: bool,
        queued: bool,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any] | None,
        error: str | None,
        duration_ms: float,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        execution_id = execution_id or str(uuid.uuid4())
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO tool_executions (
                    id, tool_name, actor, agent_name, task_id, status, mode, risk_level, approval_requirement,
                    async_mode, queued, input_json, output_json, error, duration_ms, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM tool_executions WHERE id = ?), ?), ?)
                """,
                (
                    execution_id,
                    tool_name,
                    actor,
                    agent_name,
                    task_id,
                    status,
                    mode,
                    risk_level,
                    approval_requirement,
                    1 if async_mode else 0,
                    1 if queued else 0,
                    json.dumps(input_payload),
                    json.dumps(output_payload) if output_payload is not None else None,
                    error,
                    duration_ms,
                    execution_id,
                    now,
                    now,
                ),
            )
        logger.log("INFO", "tools.execution_recorded", "Recorded tool execution.", {"execution_id": execution_id, "tool_name": tool_name, "status": status})
        return self.get(execution_id)

    def get(self, execution_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tool_executions WHERE id = ?", (execution_id,)).fetchone()
        if row is None:
            raise ValueError(f"Tool execution not found: {execution_id}")
        return self._row_to_record(row)

    def list(self, tool_name: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM tool_executions"
        params: list[Any] = []
        if tool_name:
            query += " WHERE tool_name = ?"
            params.append(tool_name)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._row_to_record(row) for row in rows]

    def analytics(self) -> dict[str, Any]:
        items = self.list(limit=500)
        by_tool = Counter(item["tool_name"] for item in items)
        by_status = Counter(item["status"] for item in items)
        durations = [item["duration_ms"] for item in items]
        return {
            "total_executions": len(items),
            "by_tool": dict(by_tool),
            "by_status": dict(by_status),
            "average_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0,
            "failures": sum(1 for item in items if item["status"] in {"failed", "blocked"}),
        }

    def health(self) -> dict[str, Any]:
        items = self.list(limit=200)
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            grouped.setdefault(item["tool_name"], []).append(item)
        health = []
        for tool_name, entries in grouped.items():
            failures = sum(1 for item in entries if item["status"] in {"failed", "blocked"})
            latest = entries[0]
            rate = failures / len(entries)
            health.append(
                {
                    "tool_name": tool_name,
                    "status": "degraded" if rate > 0.4 else "healthy",
                    "failure_rate": round(rate, 4),
                    "last_status": latest["status"],
                    "last_duration_ms": latest["duration_ms"],
                }
            )
        return {"tools": health}

    def _row_to_record(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "tool_name": row["tool_name"],
            "actor": row["actor"],
            "agent_name": row["agent_name"],
            "task_id": row["task_id"],
            "status": row["status"],
            "mode": row["mode"],
            "risk_level": row["risk_level"],
            "approval_requirement": row["approval_requirement"],
            "async_mode": bool(row["async_mode"]),
            "queued": bool(row["queued"]),
            "input": json.loads(row["input_json"]),
            "output": json.loads(row["output_json"]) if row["output_json"] else None,
            "error": row["error"],
            "duration_ms": row["duration_ms"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


tool_execution_store = ToolExecutionStore(settings.DATABASE_PATH)
