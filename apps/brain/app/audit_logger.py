from typing import Any

from app.logger import logger


class AuditLogger:
    def record(self, event: str, message: str, payload: dict[str, Any] | None = None) -> None:
        logger.log("INFO", f"audit.{event}", message, payload or {})


audit_logger = AuditLogger()
