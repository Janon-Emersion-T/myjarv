from app.tools.registry import tool_registry


def load_tools_for_task(task: dict) -> list[dict]:
    tools = tool_registry.list_tools()
    agent_tools = {tool.lower() for tool in task["selected_agent"].get("tools", [])}
    selected = []
    for tool in tools:
        if tool["name"].lower() in agent_tools or tool["approval_requirement"] == "LOW":
            selected.append(tool)
    return selected or tools[:3]
