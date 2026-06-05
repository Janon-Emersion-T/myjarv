import json
from pathlib import Path
from typing import Any


class ModelConfig:
    def __init__(self) -> None:
        self.root_path = Path(__file__).resolve().parents[4]
        self.config_path = self.root_path / "configs" / "models" / "routing.json"
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Model routing config not found: {self.config_path}")

        with self.config_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def get_ollama_base_url(self) -> str:
        return self.data.get("ollama_base_url", "http://localhost:11434")

    def get_model_by_role(self, role: str) -> dict[str, Any]:
        models = self.data.get("models", {})
        if role not in models:
            raise ValueError(f"Unknown model role: {role}")
        return models[role]

    def get_model_for_agent(self, agent_name: str) -> dict[str, Any]:
        agent_map = self.data.get("agent_model_map", {})
        model_role = agent_map.get(agent_name, "orchestrator")
        return self.get_model_by_role(model_role)