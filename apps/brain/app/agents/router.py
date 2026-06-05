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

INTENT_RULES = {
    "development": {"keywords": {"code", "repository", "bug", "fix", "laravel", "react", "api", "architecture"}},
    "marketing": {"keywords": {"campaign", "seo", "blog", "ads", "social", "content", "youtube", "tiktok"}},
    "finance": {"keywords": {"invoice", "quotation", "finance", "payment", "budget", "pricing"}},
    "legal": {"keywords": {"contract", "policy", "legal", "privacy", "terms"}},
    "operations": {"keywords": {"report", "workflow", "schedule", "operations", "daily", "weekly"}},
    "support": {"keywords": {"support", "customer", "reply", "complaint", "ticket"}},
    "research": {"keywords": {"research", "compare", "analysis", "market", "trusted"}},
    "creative": {"keywords": {"image", "video", "design", "brand", "thumbnail"}},
    "infrastructure": {"keywords": {"server", "deploy", "nginx", "docker", "dns", "domain", "cloudflare"}},
}

SUPPORTING_AGENT_MAP = {
    "development": ["Tony", "Linus"],
    "marketing": ["Analyst", "Natasha"],
    "finance": ["Ledger"],
    "legal": ["Hill"],
    "operations": ["Friday", "Oracle"],
    "support": ["Pepper"],
    "research": ["Vision"],
    "creative": ["Nova"],
    "infrastructure": ["Gatekeeper", "Sentinel"],
    "general": ["Athena"],
}

PRIORITY_KEYWORDS = {
    5: {"urgent", "critical", "asap", "outage", "production", "blocked"},
    4: {"today", "important", "deadline", "review"},
    3: {"plan", "prepare", "draft"},
}


def classify_intent(message: str) -> str:
    text = message.lower()
    best_category = "general"
    best_score = 0
    for category, config in INTENT_RULES.items():
        score = sum(1 for keyword in config["keywords"] if keyword in text)
        if score > best_score:
            best_score = score
            best_category = category
    return best_category


def classify_priority(message: str, agent: Agent) -> int:
    text = message.lower()
    for priority, keywords in PRIORITY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return max(priority, agent.priority)
    return max(3, agent.priority)


def supporting_agents_for_intent(intent_category: str, primary_agent: Agent) -> list[Agent]:
    candidates = SUPPORTING_AGENT_MAP.get(intent_category, SUPPORTING_AGENT_MAP["general"])
    agents: list[Agent] = []
    for name in candidates:
        if name == primary_agent.name:
            continue
        agents.append(get_agent_by_name(name))
    return agents


def select_agent(message: str, preferred_agent: str | None = None) -> Agent:
    if preferred_agent:
        return get_agent_by_name(preferred_agent)

    text = message.lower()

    for keyword, agent_name in KEYWORD_MAP.items():
        if keyword in text:
            return get_agent_by_name(agent_name)

    return get_agent_by_name("Jarvis")
