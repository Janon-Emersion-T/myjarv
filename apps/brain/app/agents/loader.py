import json
from pathlib import Path

from app.agents.schema import AgentDefinition

ROOT_DIR = Path(__file__).resolve().parents[4]
AGENTS_DIR = ROOT_DIR / "packages" / "agents"
REGISTRY_PATH = AGENTS_DIR / "registry.json"
PROMPTS_DIR = AGENTS_DIR / "prompts"
BASE_TEMPLATE_PATH = AGENTS_DIR / "templates" / "base_agent.md"


class AgentLoader:
    def __init__(self):
        self.agents = self._load_registry()

    def _load_registry(self) -> list[AgentDefinition]:
        if not REGISTRY_PATH.exists():
            raise FileNotFoundError(f"Missing agent registry: {REGISTRY_PATH}")

        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        return [AgentDefinition(**agent) for agent in data.get("agents", [])]

    def all(self) -> list[AgentDefinition]:
        return self.agents

    def find_by_name(self, name: str) -> AgentDefinition | None:
        needle = name.lower().strip()
        for agent in self.agents:
            if agent.name.lower() == needle:
                return agent
        return None

    def find_by_role(self, role: str) -> AgentDefinition | None:
        needle = role.lower().strip()
        for agent in self.agents:
            if agent.role.lower() == needle:
                return agent
        return None

    def load_prompt(self, agent: AgentDefinition) -> str:
        base_template = BASE_TEMPLATE_PATH.read_text(encoding="utf-8")

        base_prompt = base_template.format(
            name=agent.name,
            role=agent.role,
            department=agent.department,
            responsibility=agent.responsibility,
        )

        prompt_path = PROMPTS_DIR / agent.prompt_file

        if prompt_path.exists():
            specialist_prompt = prompt_path.read_text(encoding="utf-8")
        else:
            specialist_prompt = ""

        return f"{base_prompt}\n\n{specialist_prompt}".strip()