from app.knowledge.loader import knowledge_loader


def load_relevant_knowledge(query: str, limit: int = 5) -> list[dict]:
    return knowledge_loader.retrieve_relevant(query=query, limit=limit)
