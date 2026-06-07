from app.knowledge.loader import knowledge_loader
from app.memory import memory_store
from app.personality import apply_personality


class ContextBuilder:
    def build(self, task: dict) -> dict:
        query = task["message"]
        selected_agent = task["selected_agent"]
        supporting_agents = task.get("supporting_agents", [])
        metadata = task.get("metadata", {})
        scopes = metadata.get("memory_scopes") or ["company", "project", "decision", "agent", "user_preference", "short_term", "long_term"]
        relevant_memory = memory_store.retrieve_relevant(query, scopes=scopes, limit=8)

        knowledge = knowledge_loader.retrieve_relevant(query, limit=5)
        personality = apply_personality(query)

        return {
            "task_id": task["id"],
            "query": query,
            "selected_agent": selected_agent,
            "supporting_agents": supporting_agents,
            "memory": relevant_memory,
            "knowledge": knowledge,
            "personality": personality,
            "metadata": metadata,
        }


context_builder = ContextBuilder()
