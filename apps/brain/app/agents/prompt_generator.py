from pathlib import Path

from app.agents.registry import AgentRegistry


class AgentPromptGenerator:
    def __init__(self) -> None:
        self.registry = AgentRegistry()
        self.root_path = Path(__file__).resolve().parents[4]
        self.template_path = self.root_path / "packages" / "agents" / "templates" / "base_agent.md"

    def generate_missing_prompts(self) -> dict[str, int | list[str]]:
        if not self.template_path.exists():
            raise FileNotFoundError(f"Base prompt template not found: {self.template_path}")

        template = self.template_path.read_text(encoding="utf-8")
        created: list[str] = []
        skipped: list[str] = []

        for agent in self.registry.agents.values():
            prompt_path = self.registry.get_prompt_path(agent.name)

            if prompt_path.exists():
                skipped.append(agent.prompt_file)
                continue

            content = template.format(
                name=agent.name,
                role=agent.role.replace("_", " "),
                department=agent.department,
                responsibility=agent.description
            )

            prompt_path.write_text(content, encoding="utf-8")
            created.append(agent.prompt_file)

        return {
            "created_count": len(created),
            "skipped_count": len(skipped),
            "created": created,
            "skipped": skipped
        }