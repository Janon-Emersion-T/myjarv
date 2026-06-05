from app.agents.registry import get_agent_by_name
from app.agents.schema import Agent
from app.routing import routing_engine


def classify_intent(message: str) -> str:
    return routing_engine.route(message=message, mode="simulation")["intent_category"]


def classify_priority(message: str, agent: Agent) -> int:
    return routing_engine.route(message=message, preferred_agent=agent.name, mode="simulation")["priority"]


def supporting_agents_for_intent(intent_category: str, primary_agent: Agent) -> list[Agent]:
    decision = routing_engine.route(
        message=intent_category,
        preferred_agent=primary_agent.name,
        metadata={"execution_strategy": "single"},
        mode="simulation",
    )
    return [get_agent_by_name(name) for name in decision["supporting_agents"]]


def select_agent(message: str, preferred_agent: str | None = None) -> Agent:
    decision = routing_engine.route(message=message, preferred_agent=preferred_agent, mode="simulation")
    return get_agent_by_name(decision["selected_agent"])
