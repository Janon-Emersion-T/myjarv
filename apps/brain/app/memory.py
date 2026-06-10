from __future__ import annotations

import json
import sqlite3
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.logger import logger
from app.secops.vault import decrypt_text, encrypt_text

VALID_SCOPES = {
    "short_term",
    "long_term",
    "company",
    "client",
    "project",
    "decision",
    "mistake",
    "agent",
    "user_preference",
    "approved_template",
    "reusable_prompt",
    "department",
    "workflow",
    "conversation",
    "task",
    "execution",
    "failure",
    "success_pattern",
    "reusable_workflow",
    "prompt_history",
    "response_history",
    "personality",
    "relationship",
    "speaking_style",
    "humor_preference",
}

SCOPE_FILES = {
    "company": "company.json",
    "project": "projects.json",
    "client": "clients.json",
    "decision": "decisions.json",
    "mistake": "errors.json",
    "approved_template": "templates.json",
    "reusable_prompt": "prompts.json",
    "workflow": "workflows.json",
    "conversation": "conversations.json",
    "task": "tasks.json",
    "execution": "executions.json",
    "failure": "failures.json",
    "success_pattern": "success_patterns.json",
    "short_term": "short_term.json",
    "long_term": "long_term.json",
    "agent": "agents.json",
    "department": "departments.json",
    "personality": "personality.json",
    "relationship": "relationships.json",
    "speaking_style": "speaking_style.json",
    "humor_preference": "humor_preferences.json",
    "user_preference": "user_preferences.json",
    "reusable_workflow": "reusable_workflows.json",
    "prompt_history": "prompt_history.json",
    "response_history": "response_history.json",
}


class MemoryStore:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_dir = Path(settings.MEMORY_DIR)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir = self.memory_dir / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir = self.memory_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._write_scope_files()

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
                    summary TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    confidence_score REAL NOT NULL DEFAULT 0.5,
                    importance_score REAL NOT NULL DEFAULT 0.5,
                    access_level TEXT NOT NULL DEFAULT 'team',
                    sensitivity TEXT NOT NULL DEFAULT 'normal',
                    department TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    expires_at TEXT,
                    encrypted INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_terms (
                    memory_id TEXT NOT NULL,
                    term TEXT NOT NULL,
                    weight REAL NOT NULL DEFAULT 1.0,
                    PRIMARY KEY (memory_id, term)
                )
                """
            )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(memory_entries)").fetchall()}
            for name, sql in {
                "summary": "ALTER TABLE memory_entries ADD COLUMN summary TEXT",
                "metadata_json": "ALTER TABLE memory_entries ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'",
                "confidence_score": "ALTER TABLE memory_entries ADD COLUMN confidence_score REAL NOT NULL DEFAULT 0.5",
                "importance_score": "ALTER TABLE memory_entries ADD COLUMN importance_score REAL NOT NULL DEFAULT 0.5",
                "access_level": "ALTER TABLE memory_entries ADD COLUMN access_level TEXT NOT NULL DEFAULT 'team'",
                "sensitivity": "ALTER TABLE memory_entries ADD COLUMN sensitivity TEXT NOT NULL DEFAULT 'normal'",
                "department": "ALTER TABLE memory_entries ADD COLUMN department TEXT",
                "status": "ALTER TABLE memory_entries ADD COLUMN status TEXT NOT NULL DEFAULT 'active'",
                "expires_at": "ALTER TABLE memory_entries ADD COLUMN expires_at TEXT",
                "encrypted": "ALTER TABLE memory_entries ADD COLUMN encrypted INTEGER NOT NULL DEFAULT 0",
            }.items():
                if name not in columns:
                    connection.execute(sql)

    def create(
        self,
        scope: str,
        key: str,
        value: str,
        tags: list[str],
        source: str | None,
        task_id: str | None,
        *,
        summary: str | None = None,
        metadata: dict[str, Any] | None = None,
        confidence_score: float = 0.7,
        importance_score: float | None = None,
        access_level: str = "team",
        sensitivity: str = "normal",
        department: str | None = None,
        expires_at: str | None = None,
        encrypted: bool | None = None,
        status: str = "active",
        record_id: str | None = None,
    ) -> dict:
        normalized_scope = scope.strip().lower()
        if normalized_scope not in VALID_SCOPES:
            raise ValueError(f"Invalid memory scope: {scope}")
        clean_key = key.strip()
        clean_value = value.strip()
        if not clean_key or not clean_value:
            raise ValueError("Memory key and value are required.")
        now = self._now()
        metadata = metadata or {}
        metadata = {**metadata, "entities": self._extract_entities(clean_key, clean_value, tags, metadata)}
        should_encrypt = bool(encrypted if encrypted is not None else sensitivity in {"restricted", "secret"})
        if importance_score is None:
            importance_score = self._importance_score(normalized_scope, tags, task_id)
        if summary is None:
            summary = self._summarize_value(clean_value)
        stored_value = encrypt_text(clean_value, settings.SECURITY_SECRET_KEY) if should_encrypt else clean_value
        record = {
            "id": record_id or str(uuid.uuid4()),
            "scope": normalized_scope,
            "key": clean_key,
            "value": clean_value,
            "stored_value": stored_value,
            "tags": sorted({tag.strip().lower() for tag in tags if tag.strip()}),
            "source": source,
            "task_id": task_id,
            "summary": summary,
            "metadata": metadata,
            "confidence_score": round(float(confidence_score), 4),
            "importance_score": round(float(importance_score), 4),
            "access_level": access_level,
            "sensitivity": sensitivity,
            "department": department,
            "status": status,
            "expires_at": expires_at,
            "encrypted": should_encrypt,
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO memory_entries (
                    id, scope, key, value, tags_json, source, task_id, summary, metadata_json,
                    confidence_score, importance_score, access_level, sensitivity, department, status,
                    expires_at, encrypted, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM memory_entries WHERE id = ?), ?), ?)
                """,
                (
                    record["id"],
                    record["scope"],
                    record["key"],
                    record["stored_value"],
                    json.dumps(record["tags"]),
                    record["source"],
                    record["task_id"],
                    record["summary"],
                    json.dumps(record["metadata"]),
                    record["confidence_score"],
                    record["importance_score"],
                    record["access_level"],
                    record["sensitivity"],
                    record["department"],
                    record["status"],
                    record["expires_at"],
                    1 if record["encrypted"] else 0,
                    record["id"],
                    now,
                    now,
                ),
            )
        self._reindex_record(record["id"], self._search_blob(record))
        self._write_scope_files()
        logger.log("INFO", "memory.created", "Created memory record.", {"memory_id": record["id"], "scope": normalized_scope})
        return self.get(record["id"])

    def get(self, record_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM memory_entries WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            raise ValueError(f"Memory record not found: {record_id}")
        return self._row_to_record(row)

    def list(self, scope: str | None = None, limit: int = 100, include_expired: bool = False) -> list[dict[str, Any]]:
        query = "SELECT * FROM memory_entries"
        params: list[Any] = []
        filters: list[str] = []
        if scope:
            filters.append("scope = ?")
            params.append(scope)
        if not include_expired:
            filters.append("(expires_at IS NULL OR expires_at > ?)")
            params.append(self._now())
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY updated_at DESC, importance_score DESC LIMIT ?"
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._row_to_record(row) for row in rows]

    def retrieve_relevant(self, query: str, scopes: list[str] | None = None, limit: int = 8) -> list[dict[str, Any]]:
        candidates = self.search(query=query, limit=limit * 3, semantic=True)
        if scopes:
            scope_set = {item.lower() for item in scopes}
            candidates = [item for item in candidates if item["scope"] in scope_set]
        return candidates[:limit]

    def search(
        self,
        *,
        query: str,
        scope: str | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
        semantic: bool = False,
    ) -> list[dict[str, Any]]:
        terms = self._tokenize(query)
        rows = self.list(scope=scope, limit=500, include_expired=False)
        if not terms:
            return rows[:limit]
        tag_set = {tag.strip().lower() for tag in (tags or []) if tag.strip()}
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            blob = self._search_blob(row).lower()
            score = 0.0
            for term in terms:
                if term in blob:
                    score += 2.0
                if term == row["scope"]:
                    score += 1.0
            if tag_set:
                score += len(tag_set.intersection(set(row["tags"]))) * 1.5
            if semantic:
                overlap = len(set(terms).intersection(set(self._tokenize(blob))))
                score += overlap * 0.35
                score += row["confidence_score"] * 0.5
                score += row["importance_score"] * 0.75
            if score > 0:
                enriched = dict(row)
                enriched["search_score"] = round(score, 4)
                scored.append((score, enriched))
        scored.sort(key=lambda item: (item[0], item[1]["importance_score"], item[1]["updated_at"]), reverse=True)
        return [item[1] for item in scored[:limit]]

    def summarize(self, scope: str | None = None, limit: int = 100) -> dict[str, Any]:
        records = self.list(scope=scope, limit=limit, include_expired=False)
        tags = Counter(tag for record in records for tag in record["tags"])
        departments = Counter((record.get("department") or "unassigned") for record in records)
        return {
            "scope": scope or "all",
            "total": len(records),
            "encrypted": sum(1 for record in records if record["encrypted"]),
            "expiring_soon": sum(1 for record in records if self._expires_within_days(record.get("expires_at"), 7)),
            "top_tags": [{"tag": tag, "count": count} for tag, count in tags.most_common(10)],
            "by_department": dict(departments),
            "high_confidence": [record["key"] for record in records if record["confidence_score"] >= 0.85][:10],
            "important_memories": [record["summary"] for record in records[:8]],
        }

    def analytics(self) -> dict[str, Any]:
        records = self.list(limit=1000, include_expired=True)
        scopes = Counter(record["scope"] for record in records)
        statuses = Counter(record.get("status", "active") for record in records)
        access_levels = Counter(record.get("access_level", "team") for record in records)
        return {
            "total_records": len(records),
            "active_records": sum(1 for record in records if not self._is_expired(record.get("expires_at"))),
            "encrypted_records": sum(1 for record in records if record["encrypted"]),
            "expired_records": sum(1 for record in records if self._is_expired(record.get("expires_at"))),
            "scopes": dict(scopes),
            "statuses": dict(statuses),
            "access_levels": dict(access_levels),
            "average_confidence": round(sum(record["confidence_score"] for record in records) / len(records), 4) if records else 0,
            "average_importance": round(sum(record["importance_score"] for record in records) / len(records), 4) if records else 0,
            "duplicates": len(self.detect_duplicates()),
            "snapshots": len(self.list_snapshots()),
            "backups": len(self.list_backups()),
        }

    def export_records(self, scope: str | None = None) -> dict[str, Any]:
        return {
            "generated_at": self._now(),
            "scope": scope or "all",
            "records": self.list(scope=scope, limit=5000, include_expired=True),
        }

    def import_records(self, records: list[dict[str, Any]], merge: bool = True) -> dict[str, Any]:
        imported = 0
        skipped = 0
        for record in records:
            existing = self._find_existing(record["scope"], record["key"], record.get("task_id"))
            if existing and not merge:
                skipped += 1
                continue
            self.create(
                scope=record["scope"],
                key=record["key"],
                value=record["value"],
                tags=record.get("tags", []),
                source=record.get("source"),
                task_id=record.get("task_id"),
                summary=record.get("summary"),
                metadata=record.get("metadata"),
                confidence_score=record.get("confidence_score", 0.7),
                importance_score=record.get("importance_score"),
                access_level=record.get("access_level", "team"),
                sensitivity=record.get("sensitivity", "normal"),
                department=record.get("department"),
                expires_at=record.get("expires_at"),
                encrypted=record.get("encrypted", False),
                status=record.get("status", "active"),
                record_id=existing["id"] if existing else record.get("id"),
            )
            imported += 1
        self._write_scope_files()
        logger.log("INFO", "memory.imported", "Imported memory records.", {"imported": imported, "skipped": skipped, "merge": merge})
        return {"imported": imported, "skipped": skipped, "merge": merge}

    def create_snapshot(self, label: str = "manual") -> dict[str, Any]:
        snapshot_id = str(uuid.uuid4())
        payload = {
            "id": snapshot_id,
            "label": label,
            "created_at": self._now(),
            "records": self.list(limit=5000, include_expired=True),
            "analytics": self.analytics(),
        }
        target = self.snapshot_dir / f"{snapshot_id}.json"
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        logger.log("INFO", "memory.snapshot_created", "Created memory snapshot.", {"snapshot_id": snapshot_id, "label": label})
        return {"id": snapshot_id, "label": label, "file_path": str(target), "created_at": payload["created_at"]}

    def list_snapshots(self) -> list[dict[str, Any]]:
        snapshots = []
        for path in sorted(self.snapshot_dir.glob("*.json"), reverse=True):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            snapshots.append({"id": payload.get("id", path.stem), "label": payload.get("label", path.stem), "file_path": str(path), "created_at": payload.get("created_at")})
        return snapshots

    def create_backup(self, label: str = "manual") -> dict[str, Any]:
        backup_id = str(uuid.uuid4())
        payload = json.dumps(self.export_records(), ensure_ascii=True).encode("utf-8")
        encrypted = encrypt_text(payload.decode("utf-8"), settings.SECURITY_SECRET_KEY)
        target = self.backup_dir / f"{backup_id}.json.enc"
        target.write_text(encrypted, encoding="utf-8")
        logger.log("INFO", "memory.backup_created", "Created encrypted memory backup.", {"backup_id": backup_id, "label": label})
        return {"id": backup_id, "label": label, "file_path": str(target), "created_at": self._now()}

    def list_backups(self) -> list[dict[str, Any]]:
        backups = []
        for path in sorted(self.backup_dir.glob("*.json.enc"), reverse=True):
            backups.append({"id": path.stem.replace(".json", ""), "file_path": str(path), "created_at": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()})
        return backups

    def restore_backup(self, backup_id: str, merge: bool = True) -> dict[str, Any]:
        target = self.backup_dir / f"{backup_id}.json.enc"
        if not target.exists():
            raise ValueError("Memory backup not found.")
        decrypted = decrypt_text(target.read_text(encoding="utf-8"), settings.SECURITY_SECRET_KEY)
        payload = json.loads(decrypted)
        restored = self.import_records(payload.get("records", []), merge=merge)
        logger.log("INFO", "memory.backup_restored", "Restored memory backup.", {"backup_id": backup_id, "merge": merge})
        return {"backup_id": backup_id, "restored": restored}

    def cleanup_expired(self) -> dict[str, Any]:
        removed = 0
        now = self._now()
        with self._connect() as connection:
            rows = connection.execute("SELECT id FROM memory_entries WHERE expires_at IS NOT NULL AND expires_at <= ?", (now,)).fetchall()
            removed = len(rows)
            for row in rows:
                connection.execute("DELETE FROM memory_terms WHERE memory_id = ?", (row["id"],))
            connection.execute("DELETE FROM memory_entries WHERE expires_at IS NOT NULL AND expires_at <= ?", (now,))
        if removed:
            self._write_scope_files()
        logger.log("INFO", "memory.cleaned", "Removed expired memory records.", {"removed": removed})
        return {"removed": removed}

    def detect_duplicates(self) -> list[dict[str, Any]]:
        seen: dict[str, dict[str, Any]] = {}
        duplicates: list[dict[str, Any]] = []
        for record in self.list(limit=5000, include_expired=True):
            fingerprint = self._fingerprint(record)
            if fingerprint in seen:
                duplicates.append({"primary_id": seen[fingerprint]["id"], "duplicate_id": record["id"], "scope": record["scope"], "key": record["key"]})
            else:
                seen[fingerprint] = record
        return duplicates

    def detect_corrupted(self) -> list[dict[str, Any]]:
        corrupted = []
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM memory_entries").fetchall()
        for row in rows:
            try:
                json.loads(row["tags_json"])
                json.loads(row["metadata_json"] or "{}")
                if row["encrypted"]:
                    decrypt_text(row["value"], settings.SECURITY_SECRET_KEY)
            except Exception as exc:
                corrupted.append({"id": row["id"], "scope": row["scope"], "key": row["key"], "error": str(exc)})
        return corrupted

    def repair(self) -> dict[str, Any]:
        repaired = 0
        for record in self.list(limit=5000, include_expired=True):
            self._reindex_record(record["id"], self._search_blob(record))
            repaired += 1
        self._write_scope_files()
        logger.log("INFO", "memory.repaired", "Repaired memory indexes and scope files.", {"repaired": repaired})
        return {"repaired": repaired, "corrupted": self.detect_corrupted()}

    def related(self, record_id: str, limit: int = 10) -> list[dict[str, Any]]:
        base = self.get(record_id)
        candidates = self.list(limit=5000, include_expired=False)
        scored: list[tuple[float, dict[str, Any]]] = []
        for candidate in candidates:
            if candidate["id"] == record_id:
                continue
            score = 0.0
            score += len(set(base["tags"]).intersection(set(candidate["tags"]))) * 2.0
            if base.get("task_id") and base.get("task_id") == candidate.get("task_id"):
                score += 3.0
            if base["scope"] == candidate["scope"]:
                score += 1.0
            if score > 0:
                enriched = dict(candidate)
                enriched["relationship_score"] = round(score, 4)
                scored.append((score, enriched))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def _find_existing(self, scope: str, key: str, task_id: str | None) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM memory_entries WHERE scope = ? AND key = ? AND COALESCE(task_id, '') = COALESCE(?, '') ORDER BY updated_at DESC LIMIT 1",
                (scope, key, task_id),
            ).fetchone()
        return None if row is None else self._row_to_record(row)

    def _reindex_record(self, record_id: str, blob: str) -> None:
        counts = Counter(self._tokenize(blob))
        with self._connect() as connection:
            connection.execute("DELETE FROM memory_terms WHERE memory_id = ?", (record_id,))
            for term, count in counts.items():
                connection.execute(
                    "INSERT OR REPLACE INTO memory_terms (memory_id, term, weight) VALUES (?, ?, ?)",
                    (record_id, term, float(count)),
                )

    def _write_scope_files(self) -> None:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in self.list(limit=5000, include_expired=True):
            grouped[record["scope"]].append(record)
        for scope, filename in SCOPE_FILES.items():
            payload = {"scope": scope, "updated_at": self._now(), "records": grouped.get(scope, [])}
            (self.memory_dir / filename).write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _row_to_record(self, row: sqlite3.Row) -> dict[str, Any]:
        raw_value = row["value"]
        encrypted = bool(row["encrypted"])
        value = decrypt_text(raw_value, settings.SECURITY_SECRET_KEY) if encrypted else raw_value
        return {
            "id": row["id"],
            "scope": row["scope"],
            "key": row["key"],
            "value": value,
            "tags": json.loads(row["tags_json"]),
            "source": row["source"],
            "task_id": row["task_id"],
            "summary": row["summary"] or self._summarize_value(value),
            "metadata": json.loads(row["metadata_json"] or "{}"),
            "confidence_score": float(row["confidence_score"] or 0.0),
            "importance_score": float(row["importance_score"] or 0.0),
            "access_level": row["access_level"] or "team",
            "sensitivity": row["sensitivity"] or "normal",
            "department": row["department"],
            "status": row["status"] or "active",
            "expires_at": row["expires_at"],
            "encrypted": encrypted,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _tokenize(self, text: str) -> list[str]:
        return [token for token in "".join(char.lower() if char.isalnum() else " " for char in text).split() if len(token) > 1]

    def _search_blob(self, record: dict[str, Any]) -> str:
        return " ".join(
            [
                str(record.get("scope", "")),
                str(record.get("key", "")),
                str(record.get("value", "")),
                str(record.get("summary", "")),
                " ".join(record.get("tags", [])),
                str(record.get("source", "")),
                json.dumps(record.get("metadata", {}), ensure_ascii=True),
            ]
        )

    def _summarize_value(self, value: str) -> str:
        compact = " ".join(value.split())
        return compact[:157] + "..." if len(compact) > 160 else compact

    def _importance_score(self, scope: str, tags: list[str], task_id: str | None) -> float:
        score = 0.5
        if scope in {"decision", "mistake", "approved_template", "reusable_prompt", "success_pattern"}:
            score += 0.3
        if task_id:
            score += 0.1
        score += min(0.2, len(tags) * 0.02)
        return min(score, 1.0)

    def _fingerprint(self, record: dict[str, Any]) -> str:
        return "|".join([record["scope"], record["key"].lower(), record["value"].strip().lower()])

    def _extract_entities(self, key: str, value: str, tags: list[str], metadata: dict[str, Any]) -> list[str]:
        entities = set(tag.strip().lower() for tag in tags if tag.strip())
        for token in self._tokenize(f"{key} {value}"):
            if len(token) >= 5:
                entities.add(token)
        for field in ("client", "project", "department"):
            if metadata.get(field):
                entities.add(str(metadata[field]).strip().lower())
        return sorted(entities)[:24]

    def _is_expired(self, expires_at: str | None) -> bool:
        return bool(expires_at and expires_at <= self._now())

    def _expires_within_days(self, expires_at: str | None, days: int) -> bool:
        if not expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(expires_at)
        except ValueError:
            return False
        remaining = expiry - datetime.now(UTC)
        return remaining.total_seconds() >= 0 and remaining.days <= days

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()


memory_store = MemoryStore(settings.DATABASE_PATH)
