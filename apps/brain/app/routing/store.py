import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.logger import logger


class RoutingTraceStore:
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
                CREATE TABLE IF NOT EXISTS routing_traces (
                    trace_id TEXT PRIMARY KEY,
                    task_id TEXT,
                    mode TEXT NOT NULL,
                    message TEXT NOT NULL,
                    requested_action TEXT,
                    preferred_agent TEXT,
                    intent_category TEXT NOT NULL,
                    selected_agent TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    is_ambiguous INTEGER NOT NULL DEFAULT 0,
                    execution_strategy TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    approval_level TEXT NOT NULL,
                    duplicate_of_task_id TEXT,
                    latency_ms REAL NOT NULL DEFAULT 0,
                    input_json TEXT NOT NULL,
                    decision_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def record(
        self,
        *,
        trace_id: str | None,
        task_id: str | None,
        mode: str,
        message: str,
        requested_action: str | None,
        preferred_agent: str | None,
        latency_ms: float,
        decision: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        now = datetime.now(UTC).isoformat()
        trace_key = trace_id or str(uuid.uuid4())
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO routing_traces (
                    trace_id, task_id, mode, message, requested_action, preferred_agent, intent_category,
                    selected_agent, confidence, is_ambiguous, execution_strategy, risk_level, approval_level,
                    duplicate_of_task_id, latency_ms, input_json, decision_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM routing_traces WHERE trace_id = ?), ?), ?)
                """,
                (
                    trace_key,
                    task_id,
                    mode,
                    message,
                    requested_action,
                    preferred_agent,
                    decision["intent_category"],
                    decision["selected_agent"],
                    decision["confidence"],
                    1 if decision.get("is_ambiguous") else 0,
                    decision["execution_strategy"],
                    decision["risk_level"],
                    decision["approval_level"],
                    decision.get("duplicate_of_task_id"),
                    latency_ms,
                    json.dumps(
                        {
                            "message": message,
                            "requested_action": requested_action,
                            "preferred_agent": preferred_agent,
                            "metadata": metadata or {},
                        }
                    ),
                    json.dumps(decision),
                    trace_key,
                    now,
                    now,
                ),
            )
        logger.log("INFO", "routing.trace_recorded", "Recorded routing trace.", {"trace_id": trace_key, "task_id": task_id})
        return trace_key

    def attach_task(self, trace_id: str, task_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE routing_traces SET task_id = ?, updated_at = ? WHERE trace_id = ?",
                (task_id, datetime.now(UTC).isoformat(), trace_id),
            )

    def get_trace(self, trace_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM routing_traces WHERE trace_id = ?", (trace_id,)).fetchone()
        if row is None:
            raise ValueError(f"Routing trace not found: {trace_id}")
        return self._row_to_trace(row)

    def get_trace_for_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM routing_traces WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
                (task_id,),
            ).fetchone()
        return None if row is None else self._row_to_trace(row)

    def list_traces(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM routing_traces ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_trace(row) for row in rows]

    def analytics(self) -> dict[str, Any]:
        traces = self.list_traces(limit=500)
        total = len(traces)
        if total == 0:
            return {
                "total_traces": 0,
                "ambiguous_routes": 0,
                "duplicates_detected": 0,
                "average_confidence": 0,
                "average_latency_ms": 0,
                "by_intent": {},
                "by_agent": {},
                "by_strategy": {},
            }

        by_intent: dict[str, int] = {}
        by_agent: dict[str, int] = {}
        by_strategy: dict[str, int] = {}
        ambiguous = 0
        duplicates = 0
        confidence_sum = 0.0
        latency_sum = 0.0
        for trace in traces:
            by_intent[trace["intent_category"]] = by_intent.get(trace["intent_category"], 0) + 1
            by_agent[trace["selected_agent"]] = by_agent.get(trace["selected_agent"], 0) + 1
            by_strategy[trace["execution_strategy"]] = by_strategy.get(trace["execution_strategy"], 0) + 1
            confidence_sum += trace["decision"]["confidence"]
            latency_sum += trace["latency_ms"]
            ambiguous += 1 if trace["decision"].get("is_ambiguous") else 0
            duplicates += 1 if trace["decision"].get("duplicate_of_task_id") else 0
        return {
            "total_traces": total,
            "ambiguous_routes": ambiguous,
            "duplicates_detected": duplicates,
            "average_confidence": round(confidence_sum / total, 4),
            "average_latency_ms": round(latency_sum / total, 2),
            "by_intent": by_intent,
            "by_agent": by_agent,
            "by_strategy": by_strategy,
        }

    def _row_to_trace(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "trace_id": row["trace_id"],
            "task_id": row["task_id"],
            "mode": row["mode"],
            "message": row["message"],
            "requested_action": row["requested_action"],
            "preferred_agent": row["preferred_agent"],
            "intent_category": row["intent_category"],
            "selected_agent": row["selected_agent"],
            "confidence": row["confidence"],
            "is_ambiguous": bool(row["is_ambiguous"]),
            "execution_strategy": row["execution_strategy"],
            "risk_level": row["risk_level"],
            "approval_level": row["approval_level"],
            "duplicate_of_task_id": row["duplicate_of_task_id"],
            "latency_ms": row["latency_ms"],
            "input": json.loads(row["input_json"]),
            "decision": json.loads(row["decision_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


routing_store = RoutingTraceStore(settings.DATABASE_PATH)
