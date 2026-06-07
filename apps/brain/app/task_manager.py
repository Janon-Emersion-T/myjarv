import json
import sqlite3
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agent_executor import agent_executor
from app.agents.registry import get_agent_by_name
from app.approval_bus import approval_bus
from app.approval_engine import approval_engine
from app.audit_logger import audit_logger
from app.collaboration import collaboration_store
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
        self.approvals_dir = Path(settings.APPROVALS_DIR)
        self.approvals_dir.mkdir(parents=True, exist_ok=True)
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
                    channel TEXT NOT NULL DEFAULT 'dashboard',
                    reviewer_role TEXT NOT NULL DEFAULT 'manager',
                    department TEXT,
                    delegated_by TEXT,
                    approval_token TEXT NOT NULL,
                    replay_hash TEXT NOT NULL,
                    written_document_json TEXT,
                    evidence_json TEXT NOT NULL DEFAULT '[]',
                    signature TEXT NOT NULL,
                    confidence_score REAL NOT NULL DEFAULT 0.0,
                    suspicious_flags_json TEXT NOT NULL DEFAULT '[]',
                    risk_context_json TEXT NOT NULL DEFAULT '{}',
                    chain_step INTEGER NOT NULL DEFAULT 1,
                    stage_label TEXT NOT NULL DEFAULT 'stage_1_of_1',
                    immutable_hash TEXT NOT NULL,
                    simulation INTEGER NOT NULL DEFAULT 0,
                    revoked_at TEXT,
                    revoked_by TEXT,
                    revoked_reason TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
                """
            )
            self._ensure_column(connection, "approvals", "channel", "TEXT NOT NULL DEFAULT 'dashboard'")
            self._ensure_column(connection, "approvals", "reviewer_role", "TEXT NOT NULL DEFAULT 'manager'")
            self._ensure_column(connection, "approvals", "department", "TEXT")
            self._ensure_column(connection, "approvals", "delegated_by", "TEXT")
            self._ensure_column(connection, "approvals", "approval_token", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "approvals", "replay_hash", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "approvals", "written_document_json", "TEXT")
            self._ensure_column(connection, "approvals", "evidence_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "approvals", "signature", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "approvals", "confidence_score", "REAL NOT NULL DEFAULT 0.0")
            self._ensure_column(connection, "approvals", "suspicious_flags_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "approvals", "risk_context_json", "TEXT NOT NULL DEFAULT '{}'")
            self._ensure_column(connection, "approvals", "chain_step", "INTEGER NOT NULL DEFAULT 1")
            self._ensure_column(connection, "approvals", "stage_label", "TEXT NOT NULL DEFAULT 'stage_1_of_1'")
            self._ensure_column(connection, "approvals", "immutable_hash", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "approvals", "simulation", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(connection, "approvals", "revoked_at", "TEXT")
            self._ensure_column(connection, "approvals", "revoked_by", "TEXT")
            self._ensure_column(connection, "approvals", "revoked_reason", "TEXT")
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_events (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    approval_id TEXT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    immutable_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_artifacts (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_controls (
                    control_key TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
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
            if record["approval_level"] != "LOW":
                policy = approval_engine.build_policy(record)
                self._insert_approval_event(
                    connection=connection,
                    task_id=record["id"],
                    approval_id=None,
                    event_type="requested",
                    actor="Jarvis",
                    payload={"policy": policy, "status": record["status"]},
                    created_at=now,
                )
        if record.get("routing", {}).get("trace_id"):
            routing_store.attach_task(record["routing"]["trace_id"], record["id"])
        task_queue.enqueue(record["id"])
        logger.log("INFO", "task.created", "Created task record.", {"task_id": record["id"], "status": record["status"]})
        audit_logger.record("task_created", "Created task record.", {"task_id": record["id"], "status": record["status"]})
        if record["approval_level"] != "LOW":
            approval_bus.publish("approval_requested", {"task_id": record["id"], "status": record["status"]})
        return self.get_task(record["id"])

    def list_tasks(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [self._hydrate_task(row) for row in rows]

    def get_task(self, task_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise ValueError(f"Task not found: {task_id}")
        return self._hydrate_task(row)

    def _hydrate_task(self, row: sqlite3.Row) -> dict[str, Any]:
        task = self._row_to_task(row)
        task["approvals"] = self.list_approvals(task["id"])
        task["history"] = self.list_history(task["id"])
        task["approval_summary"] = approval_engine.summarize(task, task["approvals"], self.get_emergency_shutdown())
        task["approval_policy"] = task["approval_summary"]["policy"]
        routing = task.get("routing") or {}
        if routing.get("trace_id"):
            task["route_trace"] = routing_store.get_trace(task["routing"]["trace_id"])
        collaboration_session = collaboration_store.get_latest_session_for_task(task["id"])
        if collaboration_session is not None:
            task["collaboration"] = collaboration_session
        return task

    def _decide(self, task_id: str, decision: str, payload: dict[str, Any]) -> dict[str, Any]:
        task = self.get_task(task_id)
        if decision == "approved" and task["status"] not in {"waiting_approval", "approved"}:
            raise TaskStateError(f"Task {task_id} is not waiting for approval.")
        if decision == "rejected" and task["status"] in {"completed", "executing"}:
            raise TaskStateError(f"Task {task_id} cannot be rejected in status {task['status']}.")

        shutdown = self.get_emergency_shutdown()
        if shutdown["active"] and decision == "approved" and not payload.get("emergency_override"):
            raise TaskStateError("Emergency approval shutdown is active.")

        existing_approvals = self.list_approvals(task_id)
        prepared = approval_engine.prepare_decision(task, existing_approvals, decision, payload)
        approval_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()

        new_status = "rejected"
        if decision == "approved":
            new_status = "approved" if prepared["fully_approved"] else "waiting_approval"

        with self._connect() as connection:
            connection.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, created_at, task_id),
            )
            connection.execute(
                """
                INSERT INTO approvals (
                    id, task_id, decision, reviewer, notes, channel, reviewer_role, department, delegated_by, approval_token,
                    replay_hash, written_document_json, evidence_json, signature, confidence_score, suspicious_flags_json,
                    risk_context_json, chain_step, stage_label, immutable_hash, simulation, revoked_at, revoked_by, revoked_reason,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval_id,
                    task_id,
                    decision,
                    payload["reviewer"],
                    payload.get("notes"),
                    prepared["channel"],
                    prepared["reviewer_role"],
                    prepared["department"],
                    prepared["delegated_by"],
                    prepared["approval_token"],
                    prepared["replay_hash"],
                    json.dumps(prepared["written_document"]) if prepared["written_document"] else None,
                    json.dumps(prepared["evidence"]),
                    prepared["signature"],
                    prepared["confidence_score"],
                    json.dumps(prepared["suspicious_flags"]),
                    json.dumps(prepared["risk_context"]),
                    prepared["chain_step"],
                    prepared["stage_label"],
                    prepared["immutable_hash"],
                    0,
                    None,
                    None,
                    None,
                    created_at,
                ),
            )
            self._insert_approval_event(
                connection=connection,
                task_id=task_id,
                approval_id=approval_id,
                event_type=decision,
                actor=payload["reviewer"],
                payload={
                    "channel": prepared["channel"],
                    "reviewer_role": prepared["reviewer_role"],
                    "department": prepared["department"],
                    "stage_label": prepared["stage_label"],
                    "confidence_score": prepared["confidence_score"],
                    "suspicious_flags": prepared["suspicious_flags"],
                    "fully_approved": prepared["fully_approved"],
                },
                created_at=created_at,
            )
            self._insert_event(
                connection=connection,
                task_id=task_id,
                status=new_status,
                actor=payload["reviewer"],
                message=self._decision_message(decision, prepared),
                payload={
                    "notes": payload.get("notes") or "",
                    "channel": prepared["channel"],
                    "reviewer_role": prepared["reviewer_role"],
                    "stage_label": prepared["stage_label"],
                    "confidence_score": prepared["confidence_score"],
                },
                created_at=created_at,
            )
            if prepared["written_document"] or prepared["evidence"]:
                self._persist_approval_artifacts(task_id, approval_id, prepared, created_at)
            if decision == "rejected":
                self._insert_approval_artifact(
                    connection=connection,
                    task_id=task_id,
                    artifact_type="quarantine",
                    payload={
                        "approval_id": approval_id,
                        "reason": payload.get("notes"),
                        "decision": decision,
                        "channel": prepared["channel"],
                    },
                    created_at=created_at,
                )
        logger.log("INFO", f"task.{decision}", f"Task {decision}.", {"task_id": task_id, "reviewer": payload["reviewer"]})
        audit_logger.record(f"task_{decision}", f"Task {decision}.", {"task_id": task_id, "reviewer": payload["reviewer"]})
        approval_bus.publish(
            f"approval_{decision}",
            {
                "task_id": task_id,
                "approval_id": approval_id,
                "status": new_status,
                "reviewer": payload["reviewer"],
                "stage_label": prepared["stage_label"],
            },
        )
        return self.get_task(task_id)

    def _decision_message(self, decision: str, prepared: dict[str, Any]) -> str:
        if decision == "rejected":
            return "Task rejected and moved to quarantine."
        if prepared["fully_approved"]:
            return "Task received final approval."
        return f"Recorded partial approval for {prepared['stage_label']}."

    def approve_task(self, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._decide(task_id, "approved", payload)

    def reject_task(self, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._decide(task_id, "rejected", payload)

    def simulate_approval(self, task_id: str, payload: dict[str, Any], decision: str = "approved") -> dict[str, Any]:
        task = self.get_task(task_id)
        return approval_engine.simulate_decision(task, self.list_approvals(task_id), decision, payload)

    def get_approval_policy(self, task_id: str) -> dict[str, Any]:
        task = self.get_task(task_id)
        return approval_engine.build_policy(task)

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
        approvals = []
        for row in rows:
            approvals.append(
                {
                    "id": row["id"],
                    "task_id": row["task_id"],
                    "decision": row["decision"],
                    "reviewer": row["reviewer"],
                    "notes": row["notes"],
                    "channel": row["channel"],
                    "reviewer_role": row["reviewer_role"],
                    "department": row["department"],
                    "delegated_by": row["delegated_by"],
                    "approval_token": row["approval_token"],
                    "replay_hash": row["replay_hash"],
                    "written_document": json.loads(row["written_document_json"]) if row["written_document_json"] else None,
                    "evidence": json.loads(row["evidence_json"]),
                    "signature": row["signature"],
                    "confidence_score": row["confidence_score"],
                    "suspicious_flags": json.loads(row["suspicious_flags_json"]),
                    "risk_context": json.loads(row["risk_context_json"]),
                    "chain_step": row["chain_step"],
                    "stage_label": row["stage_label"],
                    "immutable_hash": row["immutable_hash"],
                    "simulation": bool(row["simulation"]),
                    "revoked_at": row["revoked_at"],
                    "revoked_by": row["revoked_by"],
                    "revoked_reason": row["revoked_reason"],
                    "created_at": row["created_at"],
                }
            )
        return approvals

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

    def list_approval_history(self, limit: int = 100, task_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM approvals"
        params: tuple[Any, ...] = ()
        if task_id:
            query += " WHERE task_id = ?"
            params = (task_id,)
        query += " ORDER BY created_at DESC LIMIT ?"
        params = (*params, limit)
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            {
                "id": row["id"],
                "task_id": row["task_id"],
                "decision": row["decision"],
                "reviewer": row["reviewer"],
                "channel": row["channel"],
                "reviewer_role": row["reviewer_role"],
                "department": row["department"],
                "confidence_score": row["confidence_score"],
                "suspicious_flags": json.loads(row["suspicious_flags_json"]),
                "revoked_at": row["revoked_at"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def list_approval_queue(self, limit: int = 100) -> list[dict[str, Any]]:
        tasks = [task for task in self.list_tasks() if task["status"] == "waiting_approval"]
        queue = []
        now = datetime.now(UTC)
        for task in tasks[:limit]:
            created_at = datetime.fromisoformat(task["created_at"])
            timeout_seconds = task["approval_policy"]["timeout_seconds"]
            seconds_open = int((now - created_at).total_seconds())
            queue.append(
                {
                    "task_id": task["id"],
                    "message": task["message"],
                    "approval_level": task["approval_level"],
                    "risk_level": task["risk_level"],
                    "status": task["status"],
                    "approval_summary": task["approval_summary"],
                    "seconds_open": seconds_open,
                    "overdue": timeout_seconds > 0 and seconds_open > timeout_seconds,
                    "retry_count": len([item for item in task["approvals"] if item["decision"] == "rejected" or item["revoked_at"]]),
                }
            )
        return queue

    def list_approval_artifacts(self, artifact_type: str, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM approval_artifacts
                WHERE artifact_type = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (artifact_type, limit),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "task_id": row["task_id"],
                "artifact_type": row["artifact_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def approval_metrics(self) -> dict[str, Any]:
        approvals = self.list_approval_history(limit=1000)
        tasks = self.list_tasks()
        channels = Counter(item["channel"] for item in approvals)
        roles = Counter(item["reviewer_role"] for item in approvals)
        decisions = Counter(item["decision"] for item in approvals)
        suspicious = sum(1 for item in approvals if item["suspicious_flags"])
        confidence_values = [item["confidence_score"] for item in approvals if item["confidence_score"] is not None]
        pending_by_level = Counter(task["approval_level"] for task in tasks if task["status"] == "waiting_approval")
        queue = self.list_approval_queue(limit=1000)
        return {
            "approvals_total": len(approvals),
            "pending_total": sum(pending_by_level.values()),
            "pending_by_level": dict(pending_by_level),
            "decisions": dict(decisions),
            "channels": dict(channels),
            "roles": dict(roles),
            "suspicious_total": suspicious,
            "revoked_total": len([item for item in approvals if item["revoked_at"]]),
            "average_confidence_score": round(sum(confidence_values) / len(confidence_values), 2) if confidence_values else 0.0,
            "overdue_total": len([item for item in queue if item["overdue"]]),
            "retries_total": sum(item["retry_count"] for item in queue),
            "quarantine_total": len(self.list_approval_artifacts("quarantine", limit=1000)),
            "archive_total": len(self.list_approval_artifacts("archive", limit=1000)),
            "emergency_shutdown": self.get_emergency_shutdown(),
        }

    def revoke_approval(self, task_id: str, approval_id: str, actor: str, reason: str) -> dict[str, Any]:
        task = self.get_task(task_id)
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM approvals WHERE id = ? AND task_id = ?", (approval_id, task_id)).fetchone()
            if row is None:
                raise ValueError(f"Approval not found: {approval_id}")
            if row["revoked_at"]:
                raise TaskStateError(f"Approval {approval_id} is already revoked.")
            revoked_at = datetime.now(UTC).isoformat()
            connection.execute(
                """
                UPDATE approvals
                SET revoked_at = ?, revoked_by = ?, revoked_reason = ?
                WHERE id = ?
                """,
                (revoked_at, actor, reason, approval_id),
            )
            active_approvals = connection.execute(
                """
                SELECT COUNT(*) AS total FROM approvals
                WHERE task_id = ? AND decision = 'approved' AND revoked_at IS NULL AND simulation = 0
                """,
                (task_id,),
            ).fetchone()["total"]
            policy = approval_engine.build_policy(task)
            if task["status"] in {"completed", "executing"}:
                new_status = "blocked"
            else:
                new_status = "approved" if active_approvals >= policy["min_approvals"] else "waiting_approval"
            connection.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (new_status, revoked_at, task_id))
            self._insert_approval_event(
                connection=connection,
                task_id=task_id,
                approval_id=approval_id,
                event_type="revoked",
                actor=actor,
                payload={"reason": reason, "new_status": new_status},
                created_at=revoked_at,
            )
            self._insert_event(
                connection=connection,
                task_id=task_id,
                status=new_status,
                actor=actor,
                message="Approval revoked.",
                payload={"approval_id": approval_id, "reason": reason},
                created_at=revoked_at,
            )
            self._insert_approval_artifact(
                connection=connection,
                task_id=task_id,
                artifact_type="archive",
                payload={"approval_id": approval_id, "reason": reason, "actor": actor, "type": "revocation"},
                created_at=revoked_at,
            )
        approval_bus.publish("approval_revoked", {"task_id": task_id, "approval_id": approval_id, "actor": actor})
        return self.get_task(task_id)

    def rollback_task(self, task_id: str, actor: str, reason: str) -> dict[str, Any]:
        task = self.get_task(task_id)
        if task["approval_level"] == "LOW":
            raise TaskStateError("Low-risk tasks do not require approval rollback.")
        if task["status"] not in {"approved", "completed", "executing", "failed", "blocked"}:
            raise TaskStateError(f"Task {task_id} is not in a rollback-eligible state.")

        rolled_at = datetime.now(UTC).isoformat()
        new_status = "blocked" if task["status"] in {"completed", "executing"} else "waiting_approval"
        with self._connect() as connection:
            connection.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (new_status, rolled_at, task_id))
            self._insert_approval_event(
                connection=connection,
                task_id=task_id,
                approval_id=None,
                event_type="rollback",
                actor=actor,
                payload={"reason": reason, "previous_status": task["status"], "new_status": new_status},
                created_at=rolled_at,
            )
            self._insert_event(
                connection=connection,
                task_id=task_id,
                status=new_status,
                actor=actor,
                message="Approval rollback triggered.",
                payload={"reason": reason, "previous_status": task["status"]},
                created_at=rolled_at,
            )
            self._insert_approval_artifact(
                connection=connection,
                task_id=task_id,
                artifact_type="archive",
                payload={"reason": reason, "actor": actor, "type": "rollback", "previous_status": task["status"]},
                created_at=rolled_at,
            )
        approval_bus.publish("approval_rollback", {"task_id": task_id, "actor": actor, "new_status": new_status})
        return self.get_task(task_id)

    def set_emergency_shutdown(self, active: bool, actor: str, reason: str) -> dict[str, Any]:
        updated_at = datetime.now(UTC).isoformat()
        payload = {"active": active, "actor": actor, "reason": reason, "updated_at": updated_at}
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO approval_controls (control_key, payload_json, updated_at)
                VALUES ('emergency_shutdown', ?, ?)
                ON CONFLICT(control_key) DO UPDATE SET payload_json = excluded.payload_json, updated_at = excluded.updated_at
                """,
                (json.dumps(payload), updated_at),
            )
        approval_bus.publish("approval_shutdown", payload)
        return payload

    def get_emergency_shutdown(self) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM approval_controls WHERE control_key = 'emergency_shutdown'"
            ).fetchone()
        if row is None:
            return {"active": False, "actor": None, "reason": None, "updated_at": None}
        return json.loads(row["payload_json"])

    def execute_task(self, task_id: str, executor: str = "Jarvis", force_retry: bool = False) -> dict[str, Any]:
        task = self.get_task(task_id)
        if task["status"] == "completed":
            return task
        if task["status"] == "rejected":
            raise TaskStateError(f"Task {task_id} was rejected and cannot be executed.")
        if task["status"] == "failed" and not force_retry:
            raise TaskStateError(f"Task {task_id} failed previously. Retry requires force_retry=true.")
        shutdown = self.get_emergency_shutdown()
        if shutdown["active"] and task["approval_level"] != "LOW":
            raise TaskStateError("Emergency approval shutdown is active.")
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

    def _persist_approval_artifacts(
        self,
        task_id: str,
        approval_id: str,
        prepared: dict[str, Any],
        created_at: str,
    ) -> None:
        task_dir = self.approvals_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = task_dir / f"{approval_id}.json"
        artifact_path.write_text(
            json.dumps(
                {
                    "approval_id": approval_id,
                    "task_id": task_id,
                    "written_document": prepared["written_document"],
                    "evidence": prepared["evidence"],
                    "signature": prepared["signature"],
                    "created_at": created_at,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

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

    def _insert_approval_event(
        self,
        connection: sqlite3.Connection,
        task_id: str,
        approval_id: str | None,
        event_type: str,
        actor: str,
        payload: dict[str, Any],
        created_at: str,
    ) -> None:
        immutable_hash = uuid.uuid5(uuid.NAMESPACE_URL, f"{task_id}:{approval_id}:{event_type}:{created_at}").hex
        connection.execute(
            """
            INSERT INTO approval_events (id, task_id, approval_id, event_type, actor, payload_json, immutable_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), task_id, approval_id, event_type, actor, json.dumps(payload), immutable_hash, created_at),
        )

    def _insert_approval_artifact(
        self,
        connection: sqlite3.Connection,
        task_id: str,
        artifact_type: str,
        payload: dict[str, Any],
        created_at: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO approval_artifacts (id, task_id, artifact_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), task_id, artifact_type, json.dumps(payload), created_at),
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
