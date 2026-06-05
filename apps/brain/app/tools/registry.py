import json
from pathlib import Path

from app.config import settings


class ToolRegistry:
    def __init__(self, tools_path: Path) -> None:
        self.tools_path = tools_path

    def list_tools(self) -> list[dict]:
        if not self.tools_path.exists():
            return []
        return json.loads(self.tools_path.read_text(encoding="utf-8")).get("tools", [])

    def get_tool(self, name: str) -> dict:
        for tool in self.list_tools():
            if tool["name"] == name:
                return tool
        raise ValueError(f"Tool not found: {name}")


tool_registry = ToolRegistry(Path(settings.KNOWLEDGE_DIR).parents[1] / "packages" / "tools" / "registry.json")
