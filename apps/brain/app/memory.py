import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.config import settings
from app.logger import logger

VALID_SCOPES = {
    "company",
    "client",
    "project",
    "decision",
    "mistake",
    "agent",
    "user_preference",
}


class MemoryStore:
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
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    source TEXT,
                    task_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, scope: str, key: str, value: str, tags: list[str], source: str | None, task_id: str | None) -> dict:
        if scope not in VALID_SCOPES:
            raise ValueError(f"Invalid memory scope: {scope}")
        now = datetime.now(UTC).isoformat()
        record = {
            "id": str(uuid.uuid4()),
            "scope": scope,
            "key": key,
            "value": value,
            "tags": tags,
            "source": source,
            "task_id": task_id,
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO memory_entries (
                    id, scope, key, value, tags_json, source, task_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record["scope"],
                    record["key"],
                    record["value"],
                    json.dumps(record["tags"]),
                    record["source"],
                    record["task_id"],
                    record["created_at"],
                    record["updated_at"],
                ),
            )
        logger.log("INFO", "memory.created", "Created memory record.", {"memory_id": record["id"], "scope": scope})
        return record

    def list(self, scope: str | None = None, limit: int = 100) -> list[dict]:
        query = "SELECT * FROM memory_entries"
        params: tuple = ()
        if scope:
            query += " WHERE scope = ?"
            params = (scope,)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params = params + (limit,)
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._row_to_record(row) for row in rows]

    def _row_to_record(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "scope": row["scope"],
            "key": row["key"],
            "value": row["value"],
            "tags": json.loads(row["tags_json"]),
            "source": row["source"],
            "task_id": row["task_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


memory_store = MemoryStore(settings.DATABASE_PATH)
