import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings


class VoiceStore:
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
                CREATE TABLE IF NOT EXISTS voice_sessions (
                    id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    locale TEXT NOT NULL,
                    speaker_id TEXT NOT NULL,
                    speaker_authorized INTEGER NOT NULL DEFAULT 1,
                    wake_word_detected INTEGER NOT NULL DEFAULT 0,
                    wake_word TEXT NOT NULL,
                    transport TEXT NOT NULL,
                    stt_provider TEXT NOT NULL,
                    tts_provider TEXT NOT NULL,
                    noise_reduction TEXT NOT NULL,
                    input_device TEXT,
                    output_device TEXT,
                    status TEXT NOT NULL,
                    current_task_id TEXT,
                    last_transcript TEXT,
                    last_response_text TEXT,
                    conversation_memory_json TEXT NOT NULL,
                    analytics_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS voice_interactions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    speaker_id TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    normalized_text TEXT NOT NULL,
                    detected_mode TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    approval_level TEXT NOT NULL,
                    response_text TEXT NOT NULL,
                    interruption_handled INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS voice_events (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO voice_sessions (
                    id, mode, locale, speaker_id, speaker_authorized, wake_word_detected, wake_word,
                    transport, stt_provider, tts_provider, noise_reduction, input_device, output_device,
                    status, current_task_id, last_transcript, last_response_text, conversation_memory_json,
                    analytics_json, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload["mode"],
                    payload["locale"],
                    payload["speaker_id"],
                    1 if payload["speaker_authorized"] else 0,
                    1 if payload["wake_word_detected"] else 0,
                    payload["wake_word"],
                    payload["transport"],
                    payload["stt_provider"],
                    payload["tts_provider"],
                    payload["noise_reduction"],
                    payload.get("input_device"),
                    payload.get("output_device"),
                    payload["status"],
                    payload.get("current_task_id"),
                    payload.get("last_transcript"),
                    payload.get("last_response_text"),
                    json.dumps(payload.get("conversation_memory", [])),
                    json.dumps(payload.get("analytics", {})),
                    json.dumps(payload.get("metadata", {})),
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )
        return self.get_session(payload["id"])

    def update_session(self, session_id: str, **changes: Any) -> dict[str, Any]:
        current = self.get_session(session_id)
        merged = {
            **current,
            **changes,
            "conversation_memory": changes.get("conversation_memory", current["conversation_memory"]),
            "analytics": changes.get("analytics", current["analytics"]),
            "metadata": changes.get("metadata", current["metadata"]),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE voice_sessions
                SET status = ?, current_task_id = ?, last_transcript = ?, last_response_text = ?,
                    conversation_memory_json = ?, analytics_json = ?, metadata_json = ?, updated_at = ?,
                    wake_word_detected = ?, speaker_authorized = ?, input_device = ?, output_device = ?
                WHERE id = ?
                """,
                (
                    merged["status"],
                    merged.get("current_task_id"),
                    merged.get("last_transcript"),
                    merged.get("last_response_text"),
                    json.dumps(merged.get("conversation_memory", [])),
                    json.dumps(merged.get("analytics", {})),
                    json.dumps(merged.get("metadata", {})),
                    merged["updated_at"],
                    1 if merged.get("wake_word_detected") else 0,
                    1 if merged.get("speaker_authorized") else 0,
                    merged.get("input_device"),
                    merged.get("output_device"),
                    session_id,
                ),
            )
        return self.get_session(session_id)

    def add_interaction(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO voice_interactions (
                    id, session_id, speaker_id, input_text, normalized_text, detected_mode, intent,
                    confidence, risk_level, approval_level, response_text, interruption_handled, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload["session_id"],
                    payload["speaker_id"],
                    payload["input_text"],
                    payload["normalized_text"],
                    payload["detected_mode"],
                    payload["intent"],
                    payload["confidence"],
                    payload["risk_level"],
                    payload["approval_level"],
                    payload["response_text"],
                    1 if payload.get("interruption_handled") else 0,
                    payload["created_at"],
                ),
            )
        return payload

    def add_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO voice_events (id, session_id, event_type, message, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload["session_id"],
                    payload["event_type"],
                    payload["message"],
                    json.dumps(payload.get("payload", {})),
                    payload["created_at"],
                ),
            )
        return payload

    def get_session(self, session_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM voice_sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise ValueError(f"Voice session not found: {session_id}")
        session = self._row_to_session(row)
        session["interactions"] = self.list_interactions(session_id)
        session["events"] = self.list_events(session_id)
        return session

    def list_sessions(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM voice_sessions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_session(row) for row in rows]

    def list_interactions(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM voice_interactions WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return [dict(row) | {"interruption_handled": bool(row["interruption_handled"])} for row in rows]

    def list_events(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM voice_events WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return [dict(row) | {"payload": json.loads(row["payload_json"])} for row in rows]

    def analytics(self) -> dict[str, Any]:
        sessions = self.list_sessions(limit=300)
        interactions = []
        for session in sessions:
            interactions.extend(self.list_interactions(session["id"]))
        if not sessions:
            return {
                "total_sessions": 0,
                "authorized_speakers": 0,
                "average_confidence": 0,
                "emergency_sessions": 0,
                "mode_counts": {},
                "tone_counts": {},
                "restricted_sessions": 0,
            }
        mode_counts: dict[str, int] = {}
        tone_counts: dict[str, int] = {}
        authorized = 0
        emergency = 0
        restricted = 0
        for session in sessions:
            mode_counts[session["mode"]] = mode_counts.get(session["mode"], 0) + 1
            authorized += 1 if session["speaker_authorized"] else 0
            emergency += 1 if session["mode"] == "emergency" else 0
            restricted += 0 if session["speaker_authorized"] else 1
            tone = str(session.get("analytics", {}).get("tone_profile", "unknown"))
            tone_counts[tone] = tone_counts.get(tone, 0) + 1
        average_confidence = (
            round(sum(item["confidence"] for item in interactions) / len(interactions), 4)
            if interactions
            else 0
        )
        return {
            "total_sessions": len(sessions),
            "authorized_speakers": authorized,
            "average_confidence": average_confidence,
            "emergency_sessions": emergency,
            "mode_counts": mode_counts,
            "tone_counts": tone_counts,
            "restricted_sessions": restricted,
        }

    def next_id(self) -> str:
        return str(uuid.uuid4())

    def now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _row_to_session(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "mode": row["mode"],
            "locale": row["locale"],
            "speaker_id": row["speaker_id"],
            "speaker_authorized": bool(row["speaker_authorized"]),
            "wake_word_detected": bool(row["wake_word_detected"]),
            "wake_word": row["wake_word"],
            "transport": row["transport"],
            "stt_provider": row["stt_provider"],
            "tts_provider": row["tts_provider"],
            "noise_reduction": row["noise_reduction"],
            "input_device": row["input_device"],
            "output_device": row["output_device"],
            "status": row["status"],
            "current_task_id": row["current_task_id"],
            "last_transcript": row["last_transcript"],
            "last_response_text": row["last_response_text"],
            "conversation_memory": json.loads(row["conversation_memory_json"]),
            "analytics": json.loads(row["analytics_json"]),
            "metadata": json.loads(row["metadata_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


voice_store = VoiceStore(settings.DATABASE_PATH)
