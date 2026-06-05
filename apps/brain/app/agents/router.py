from app.agents.registry import list_agents, get_agent_by_name
from app.agents.schema import Agent


KEYWORD_MAP = {
    "laravel": "Lara",
    "blade": "Lara",
    "livewire": "Lara",
    "seo": "Neil",
    "marketing": "Maya",
    "facebook": "Meta",
    "instagram": "Meta",
    "linkedin": "LinkedIn",
    "twitter": "Xavier",
    "x ": "Xavier",
    "youtube": "YouTube",
    "whatsapp": "WhatsApp",
    "api": "Api",
    "database": "Diana",
    "mysql": "Myra",
    "postgres": "Postgres",
    "docker": "Docker",
    "nginx": "Nginx",
    "security": "VictorSec",
    "ui": "Uma",
    "ux": "Uma",
    "figma": "Figma",
    "pos": "Pos",
    "crm": "Crm",
    "erp": "Erp",
    "content": "Natasha",
    "blog": "Blake",
    "contract": "Lawrence",
    "quote": "Morgan",
    "invoice": "Morgan",
}


def select_agent(message: str, preferred_agent: str | None = None) -> Agent:
    if preferred_agent:
        return get_agent_by_name(preferred_agent)

    text = message.lower()

    for keyword, agent_name in KEYWORD_MAP.items():
        if keyword in text:
            return get_agent_by_name(agent_name)

    return get_agent_by_name("Jarvis")