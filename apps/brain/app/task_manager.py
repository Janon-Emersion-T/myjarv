import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agent_executor import agent_executor
from app.agents.registry import get_agent_by_name
from app.audit_logger import audit_logger
from app.config import settings
from app.exceptions import ApprovalRequiredError, TaskExecutionError, TaskStateError
from app.logger import logger
from app.orchestrator import _to_summary
from app.response_formatter import response_formatter
from app.routing import routing_engine, routing_store
from app.result_reviewer import result_reviewer
from app.safety import is_execution_allowed, should_retry
from app.task_queue import task_queue


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
                    reasoning TEXT NOT NULL,
                    routing_json TEXT,
                    execution_result_json TEXT,
                    review_result_json TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT
                )
                """
            )
            self._ensure_column(connection, "tasks", "intent_category", "TEXT NOT NULL DEFAULT 'general'")
            self._ensure_column(connection, "tasks", "supporting_agents_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "tasks", "priority", "INTEGER NOT NULL DEFAULT 3")
            self._ensure_column(connection, "tasks", "routing_json", "TEXT")
            self._ensure_column(connection, "tasks", "execution_result_json", "TEXT")
            self._ensure_column(connection, "tasks", "review_result_json", "TEXT")
            self._ensure_column(connection, "tasks", "retry_count", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(connection, "tasks", "last_error", "TEXT")
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS task_events (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
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
                    supporting_agents_json, requested_action, priority, risk_level, approval_level, status, metadata_json, reasoning,
                    routing_json, execution_result_json, review_result_json, retry_count, last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    json.dumps(record.get("routing")) if record.get("routing") else None,
                    None,
                    None,
                    0,
                    None,
                ),
            )
            for event in record.get("history", []):
                self._insert_event(
                    connection=connection,
                    task_id=record["id"],
                    status=event["status"],
                    actor=event["actor"],
                    message=event["message"],
                    payload=event.get("payload", {}),
                    created_at=event["created_at"],
                )
        if record.get("routing", {}).get("trace_id"):
            routing_store.attach_task(record["routing"]["trace_id"], record["id"])
        task_queue.enqueue(record["id"])
        logger.log("INFO", "task.created", "Created task record.", {"task_id": record["id"], "status": record["status"]})
        audit_logger.record("task_created", "Created task record.", {"task_id": record["id"], "status": record["status"]})
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
        task["history"] = self.list_history(task_id)
        if task.get("routing", {}).get("trace_id"):
            task["route_trace"] = routing_store.get_trace(task["routing"]["trace_id"])
        return task

    def _decide(self, task_id: str, decision: str, reviewer: str, notes: str | None) -> dict[str, Any]:
        task = self.get_task(task_id)
        if task["status"] not in {"waiting_approval", "approved"} and decision == "approved":
            raise TaskStateError(f"Task {task_id} is not waiting for approval.")
        if task["status"] in {"completed", "executing"}:
            raise TaskStateError(f"Task {task_id} cannot be {decision} in status {task['status']}.")

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
            self._insert_event(
                connection=connection,
                task_id=task_id,
                status=new_status,
                actor=reviewer,
                message=f"Task {decision} by {reviewer}.",
                payload={"notes": notes or ""},
                created_at=created_at,
            )
        logger.log("INFO", f"task.{decision}", f"Task {decision}.", {"task_id": task_id, "reviewer": reviewer})
        audit_logger.record(f"task_{decision}", f"Task {decision}.", {"task_id": task_id, "reviewer": reviewer})
        return self.get_task(task_id)

    def approve_task(self, task_id: str, reviewer: str, notes: str | None) -> dict[str, Any]:
        return self._decide(task_id, "approved", reviewer, notes)

    def reject_task(self, task_id: str, reviewer: str, notes: str | None) -> dict[str, Any]:
        return self._decide(task_id, "rejected", reviewer, notes)

    def reassign_task(self, task_id: str, reviewer: str, agent_name: str, reason: str) -> dict[str, Any]:
        task = self.get_task(task_id)
        route = routing_engine.route(
            message=task["message"],
            requested_action=task.get("requested_action"),
            preferred_agent=agent_name,
            metadata={
                **task.get("metadata", {}),
                "task_id": task_id,
                "route_override": agent_name,
                "reassignment_reason": reason,
                "previous_trace_id": task.get("routing", {}).get("trace_id"),
            },
        )
        selected_agent = get_agent_by_name(route["selected_agent"])
        supporting_agents = [_to_summary(get_agent_by_name(name)).model_dump() for name in route["supporting_agents"]]
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET updated_at = ?, preferred_agent = ?, selected_agent_json = ?, supporting_agents_json = ?,
                    priority = ?, risk_level = ?, approval_level = ?, reasoning = ?, routing_json = ?, status = ?
                WHERE id = ?
                """,
                (
                    now,
                    agent_name,
                    json.dumps(_to_summary(selected_agent).model_dump()),
                    json.dumps(supporting_agents),
                    route["priority"],
                    route["risk_level"],
                    route["approval_level"],
                    route["reasoning"],
                    json.dumps(route),
                    "waiting_approval" if route["approval_level"] != "LOW" else "routed",
                    task_id,
                ),
            )
            self._insert_event(
                connection=connection,
                task_id=task_id,
                status="routed",
                actor=reviewer,
                message=f"Task manually reassigned to {selected_agent.name}.",
                payload={"reason": reason, "trace_id": route["trace_id"], "reassigned_to": selected_agent.name},
                created_at=now,
            )
        audit_logger.record(
            "task_reassigned",
            "Task manually reassigned.",
            {"task_id": task_id, "reviewer": reviewer, "agent": selected_agent.name},
        )
        return self.get_task(task_id)

    def list_approvals(self, task_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM approvals WHERE task_id = ? ORDER BY created_at DESC",
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_history(self, task_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM task_events WHERE task_id = ? ORDER BY created_at ASC",
                (task_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "task_id": row["task_id"],
                "status": row["status"],
                "actor": row["actor"],
                "message": row["message"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def execute_task(self, task_id: str, executor: str = "Jarvis", force_retry: bool = False) -> dict[str, Any]:
        task = self.get_task(task_id)
        if task["status"] == "completed":
            return task
        if task["status"] == "rejected":
            raise TaskStateError(f"Task {task_id} was rejected and cannot be executed.")
        if task["status"] == "failed" and not force_retry:
            raise TaskStateError(f"Task {task_id} failed previously. Retry requires force_retry=true.")
        if not is_execution_allowed(task):
            raise ApprovalRequiredError(f"Task {task_id} requires approval before execution.")

        if task["status"] == "failed" and not should_retry(task):
            raise TaskExecutionError(f"Task {task_id} exceeded retry allowance.")

        now = datetime.now(UTC).isoformat()
        retry_count = task.get("retry_count", 0) + (1 if task["status"] == "failed" else 0)

        with self._connect() as connection:
            connection.execute(
                "UPDATE tasks SET status = ?, updated_at = ?, retry_count = ? WHERE id = ?",
                ("executing", now, retry_count, task_id),
            )
            self._insert_event(
                connection=connection,
                task_id=task_id,
                status="executing",
                actor=executor,
                message=f"Execution started by {executor}.",
                payload={"force_retry": force_retry, "retry_count": retry_count},
                created_at=now,
            )
        audit_logger.record("task_executing", "Task execution started.", {"task_id": task_id, "executor": executor})

        try:
            response = agent_executor.execute(self.get_task(task_id))
        except Exception as exc:
            return self._handle_execution_failure(task_id, executor, str(exc), retry_count)

        formatted_response = response_formatter.format_execution(response)
        review = result_reviewer.review(self.get_task(task_id), response)
        completion_time = datetime.now(UTC).isoformat()
        final_status = review.recommended_status

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET status = ?, updated_at = ?, execution_result_json = ?, review_result_json = ?, retry_count = ?, last_error = NULL
                WHERE id = ?
                """,
                (
                    final_status,
                    completion_time,
                    json.dumps(formatted_response),
                    json.dumps(response_formatter.format_review(review)),
                    retry_count,
                    task_id,
                ),
            )
            self._insert_event(
                connection=connection,
                task_id=task_id,
                status=final_status,
                actor=executor,
                message=f"Execution finished with status {final_status}.",
                payload={"review_score": review.score, "review_verdict": review.verdict},
                created_at=completion_time,
            )
        task_queue.remove(task_id)
        audit_logger.record(
            "task_executed",
            "Task execution finished.",
            {"task_id": task_id, "status": final_status, "review_score": review.score},
        )
        return self.get_task(task_id)

    def _handle_execution_failure(self, task_id: str, executor: str, error: str, retry_count: int) -> dict[str, Any]:
        failed_at = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                "UPDATE tasks SET status = ?, updated_at = ?, retry_count = ?, last_error = ? WHERE id = ?",
                ("failed", failed_at, retry_count, error, task_id),
            )
            self._insert_event(
                connection=connection,
                task_id=task_id,
                status="failed",
                actor=executor,
                message="Task execution failed.",
                payload={"error": error, "retry_count": retry_count},
                created_at=failed_at,
            )
        audit_logger.record("task_failed", "Task execution failed.", {"task_id": task_id, "error": error})
        return self.get_task(task_id)

    def _insert_event(
        self,
        connection: sqlite3.Connection,
        task_id: str,
        status: str,
        actor: str,
        message: str,
        payload: dict[str, Any],
        created_at: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO task_events (id, task_id, status, actor, message, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), task_id, status, actor, message, json.dumps(payload), created_at),
        )

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
            "routing": json.loads(row["routing_json"]) if row["routing_json"] else None,
            "execution_result": json.loads(row["execution_result_json"]) if row["execution_result_json"] else None,
            "review_result": json.loads(row["review_result_json"]) if row["review_result_json"] else None,
            "retry_count": row["retry_count"],
            "last_error": row["last_error"],
        }


task_manager = TaskManager(settings.DATABASE_PATH)
