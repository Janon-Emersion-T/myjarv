from app.agents.registry import AgentRegistry
from app.services.ollama_service import OllamaService


class AgentService:
    def __init__(self) -> None:
        self.registry = AgentRegistry()
        self.ollama = OllamaService()

    def list_available_agents(self) -> list[dict[str, str]]:
        return self.registry.list_agents()

    def list_agents_by_department(self, department: str) -> list[dict[str, str]]:
        return self.registry.list_by_department(department)

    def load_agent_prompt(self, agent_name: str) -> str:
        prompt_path = self.registry.get_prompt_path(agent_name)

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found for agent {agent_name}: {prompt_path}")

        return prompt_path.read_text(encoding="utf-8")

    async def ask_agent(self, agent_name: str, message: str) -> dict[str, str]:
        agent = self.registry.get_agent(agent_name)
        system_prompt = self.load_agent_prompt(agent_name)

        response = await self.ollama.chat_by_model_role(
            model_role=agent.model_role,
            user_message=message,
            system_message=system_prompt
        )

        return {
            "agent": agent.name,
            "role": agent.role,
            "department": agent.department,
            "model_role": agent.model_role,
            "response": response
        }