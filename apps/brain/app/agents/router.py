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
    "api": "Fury",
    "database": "Diana",
    "mysql": "Myra",
    "postgres": "Postgres",
    "docker": "Docker",
    "nginx": "Nginx",
    "security": "VictorSec",
    "ui": "Uma",
    "ux": "Uma",
    "figma": "Figma",
    "pos": "Gambit",
    "crm": "Mantis",
    "erp": "Forge",
    "content": "Natasha",
    "blog": "Blake",
    "contract": "Lawrence",
    "quote": "Morgan",
    "invoice": "Morgan",
    "email": "Raven",
    "voice": "Canary",
    "domain": "Constantine",
    "dns": "Constantine",
    "git": "Bishop",
    "image": "Mystique",
    "video": "Quicksilver",
    "prompt": "Wanda",
    "model": "Strange",
    "documentation": "Lois",
    "docs": "Lois",
    "policy": "Hill",
    "recruit": "Moira",
    "hiring": "Moira",
    "admin": "Coulson",
    "schedule": "Tempus",
    "calendar": "Tempus",
    "automation": "Cisco",
}


def select_agent(message: str, preferred_agent: str | None = None) -> Agent:
    if preferred_agent:
        return get_agent_by_name(preferred_agent)

    text = message.lower()

    for keyword, agent_name in KEYWORD_MAP.items():
        if keyword in text:
            return get_agent_by_name(agent_name)

    return get_agent_by_name("Jarvis")
