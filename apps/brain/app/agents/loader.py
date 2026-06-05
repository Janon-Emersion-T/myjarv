from pathlib import Path
from app.agents.schema import Agent


ROOT_DIR = Path(__file__).resolve().parents[4]
PROMPTS_DIR = ROOT_DIR / "packages" / "agents" / "prompts"


def load_agent_prompt(agent: Agent) -> str:
    prompt_path = PROMPTS_DIR / agent.prompt_file

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file missing: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")
