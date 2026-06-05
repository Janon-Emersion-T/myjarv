from app.agents.loader import AgentLoader
from app.agents.schema import AgentDefinition

loader = AgentLoader()


KEYWORD_AGENT_MAP = {
    "laravel": "Lara",
    "livewire": "Lara",
    "filament": "Lara",
    "php": "Lara",
    "vue": "Victor",
    "nuxt": "Victor",
    "react": "Rhea",
    "next": "Rhea",
    "frontend": "Taylor",
    "ui": "Uma",
    "ux": "Uma",
    "database": "Diana",
    "mysql": "Myra",
    "postgres": "Postgres",
    "seo": "Neil",
    "content": "Natasha",
    "blog": "Blake",
    "marketing": "Maya",
    "facebook": "Meta",
    "instagram": "Meta",
    "linkedin": "LinkedIn",
    "tiktok": "Tiktok",
    "youtube": "YouTube",
    "sales": "Sasha",
    "customer": "Pepper",
    "quote": "Morgan",
    "invoice": "Morgan",
    "contract": "Lawrence",
    "policy": "Policy",
    "docker": "Docker",
    "nginx": "Nginx",
    "server": "Rhodes",
    "deploy": "Rhodes",
    "security": "VictorSec",
    "test": "Bruce",
    "qa": "Bruce",
    "pos": "Pos",
    "erp": "Erp",
    "crm": "Crm",
    "wordpress": "Wordpress",
    "shopify": "Shopify",
    "whatsapp": "WhatsApp",
    "email": "Email",
    "rag": "Rag",
    "embedding": "Vector",
    "prompt": "Prompt",
    "agent": "Aiden",
}


def select_agent(message: str, preferred_agent: str | None = None) -> AgentDefinition:
    if preferred_agent:
        agent = loader.find_by_name(preferred_agent)
        if agent:
            return agent

    text = message.lower()

    for keyword, agent_name in KEYWORD_AGENT_MAP.items():
        if keyword in text:
            agent = loader.find_by_name(agent_name)
            if agent:
                return agent

    fallback = loader.find_by_name("Jarvis")
    if fallback:
        return fallback

    raise RuntimeError("Jarvis agent is missing from registry.json")