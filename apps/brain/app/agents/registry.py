import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AgentDefinition:
    name: str
    role: str
    department: str
    model_role: str
    prompt_file: str
    description: str
    responsibility: str


class AgentRegistry:
    def __init__(self) -> None:
        self.root_path = Path(__file__).resolve().parents[4]
        self.registry_path = self.root_path / "packages" / "agents" / "registry.json"
        self.prompts_path = self.root_path / "packages" / "agents" / "prompts"
        self.agents = self._load_agents()

    def _load_agents(self) -> dict[str, AgentDefinition]:
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Agent registry not found: {self.registry_path}")

        with self.registry_path.open("r", encoding="utf-8") as file:
            data: dict[str, Any] = json.load(file)

        agents: dict[str, AgentDefinition] = {}

        for item in data.get("agents", []):
            agent = AgentDefinition(
                name=item["name"],
                role=item["role"],
                department=item["department"],
                model_role=item["model_role"],
                prompt_file=item["prompt_file"],
                description=item["description"],
                responsibility=item.get("responsibility", item["description"]),
            )
            agents[agent.name] = agent

        return agents

    def get_agent(self, agent_name: str) -> AgentDefinition:
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        return self.agents[agent_name]

    def list_agents(self) -> list[dict[str, str]]:
        return [
            {
                "name": agent.name,
                "role": agent.role,
                "department": agent.department,
                "model_role": agent.model_role,
                "description": agent.description,
            }
            for agent in self.agents.values()
        ]

    def list_by_department(self, department: str) -> list[dict[str, str]]:
        return [
            {
                "name": agent.name,
                "role": agent.role,
                "department": agent.department,
                "model_role": agent.model_role,
                "description": agent.description,
            }
            for agent in self.agents.values()
            if agent.department == department
        ]

    def get_prompt_path(self, agent_name: str) -> Path:
        agent = self.get_agent(agent_name)
        return self.prompts_path / agent.prompt_file