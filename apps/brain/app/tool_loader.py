from app.tools.registry import tool_registry


def load_tools_for_task(task: dict) -> list[dict]:
    selected_agent = task["selected_agent"]
    compatible = tool_registry.compatible_tools_for_agent(selected_agent["name"], selected_agent.get("tools", []))
    return compatible or tool_registry.list_tools()[:4]
