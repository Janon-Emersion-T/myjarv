from app.knowledge.loader import knowledge_loader
from app.memory import memory_store
from app.personality import apply_personality


class ContextBuilder:
    def build(self, task: dict) -> dict:
        query = task["message"]
        selected_agent = task["selected_agent"]
        supporting_agents = task.get("supporting_agents", [])

        relevant_memory = []
        for scope in ("company", "project", "decision", "agent", "user_preference"):
            relevant_memory.extend(memory_store.list(scope=scope, limit=2))

        knowledge = knowledge_loader.retrieve_relevant(query, limit=5)
        personality = apply_personality(query)

        return {
            "task_id": task["id"],
            "query": query,
            "selected_agent": selected_agent,
            "supporting_agents": supporting_agents,
            "memory": relevant_memory[:8],
            "knowledge": knowledge,
            "personality": personality,
            "metadata": task.get("metadata", {}),
        }


context_builder = ContextBuilder()
