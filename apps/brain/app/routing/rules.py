import json
from pathlib import Path
from typing import Any

from app.config import settings


class RoutingRules:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            raise FileNotFoundError(f"Routing rules not found: {self.path}")
        return json.loads(self.path.read_text(encoding="utf-8"))


routing_rules = RoutingRules(settings.ROUTING_RULES_PATH)
