import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from app.config import settings


class JarvisLogger:
    def __init__(self, log_path: str) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, level: str, event: str, message: str, payload: dict[str, Any] | None = None) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level.upper(),
            "event": event,
            "message": message,
            "payload": payload or {},
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    def read_recent(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []

        with self.log_path.open("r", encoding="utf-8") as handle:
            lines = [line.strip() for line in handle.readlines() if line.strip()]

        selected = lines[-(limit or settings.DEFAULT_LOG_LIMIT):]
        return [json.loads(line) for line in selected]


logger = JarvisLogger(settings.LOG_FILE_PATH)
