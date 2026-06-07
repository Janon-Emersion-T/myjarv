from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agents.registry import list_agents
from app.config import settings


VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_MODES = {"read", "write", "plan"}
VALID_STATUSES = {"active", "deprecated", "experimental"}


class ToolRegistry:
    def __init__(self, tools_path: Path, schema_path: Path) -> None:
        self.tools_path = tools_path
        self.schema_path = schema_path

    def load(self) -> dict[str, Any]:
        if not self.tools_path.exists():
            return {"version": "0.0.0", "updated_at": None, "tools": []}
        payload = json.loads(self.tools_path.read_text(encoding="utf-8"))
        self.validate(payload)
        return payload

    def list_tools(self, *, include_deprecated: bool = False) -> list[dict[str, Any]]:
        tools = self.load()["tools"]
        if include_deprecated:
            return tools
        return [tool for tool in tools if tool["status"] != "deprecated"]

    def get_tool(self, name: str) -> dict[str, Any]:
        lowered = name.lower()
        for tool in self.list_tools(include_deprecated=True):
            aliases = {alias.lower() for alias in tool.get("aliases", [])}
            if tool["name"].lower() == lowered or lowered in aliases:
                return tool
        raise ValueError(f"Tool not found: {name}")

    def validate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or json.loads(self.tools_path.read_text(encoding="utf-8"))
        schema = json.loads(self.schema_path.read_text(encoding="utf-8")) if self.schema_path.exists() else {}
        issues: list[dict[str, Any]] = []
        for field in schema.get("required_top_level", []):
            if field not in payload:
                issues.append({"field": field, "issue": "missing_top_level_field"})
        names = set()
        aliases = set()
        for tool in payload.get("tools", []):
            for field in schema.get("required_tool_fields", []):
                if field not in tool:
                    issues.append({"tool": tool.get("name", "<unknown>"), "field": field, "issue": "missing_required_field"})
            name = tool.get("name", "")
            if name in names:
                issues.append({"tool": name, "issue": "duplicate_name"})
            names.add(name)
            for alias in tool.get("aliases", []):
                if alias in aliases:
                    issues.append({"tool": name, "alias": alias, "issue": "duplicate_alias"})
                aliases.add(alias)
            if tool.get("risk_level") not in VALID_RISK_LEVELS:
                issues.append({"tool": name, "field": "risk_level", "issue": "invalid_value"})
            if tool.get("approval_requirement") not in VALID_RISK_LEVELS:
                issues.append({"tool": name, "field": "approval_requirement", "issue": "invalid_value"})
            if tool.get("mode") not in VALID_MODES:
                issues.append({"tool": name, "field": "mode", "issue": "invalid_value"})
            if tool.get("status") not in VALID_STATUSES:
                issues.append({"tool": name, "field": "status", "issue": "invalid_value"})
        return {"valid": len(issues) == 0, "issues": issues, "tool_count": len(payload.get("tools", []))}

    def capabilities(self) -> dict[str, Any]:
        by_category: dict[str, list[str]] = {}
        by_mode: dict[str, list[str]] = {}
        integrations: dict[str, list[str]] = {}
        for tool in self.list_tools():
            by_category.setdefault(tool["category"], []).append(tool["name"])
            by_mode.setdefault(tool["mode"], []).append(tool["name"])
            integrations.setdefault(tool["integration"], []).append(tool["name"])
        return {
            "version": self.load()["version"],
            "by_category": by_category,
            "by_mode": by_mode,
            "integrations": integrations,
        }

    def compatible_tools_for_agent(self, agent_name: str, declared_tools: list[str]) -> list[dict[str, Any]]:
        selected = []
        declared = {item.lower() for item in declared_tools}
        for tool in self.list_tools():
            aliases = {alias.lower() for alias in tool.get("aliases", [])}
            if tool["name"].lower() in declared or declared.intersection(aliases):
                selected.append(tool)
        if selected:
            return selected
        return [tool for tool in self.list_tools() if tool["approval_requirement"] == "LOW"][:6]

    def compatibility_matrix(self) -> dict[str, Any]:
        matrix = []
        for agent in list_agents():
            compatible = self.compatible_tools_for_agent(agent.name, agent.tools)
            matrix.append(
                {
                    "agent": agent.name,
                    "department": agent.department,
                    "declared_tools": agent.tools,
                    "compatible_tools": [tool["name"] for tool in compatible],
                }
            )
        return {"matrix": matrix}


ROOT = Path(settings.KNOWLEDGE_DIR).parents[1]
tool_registry = ToolRegistry(ROOT / "packages" / "tools" / "registry.json", ROOT / "packages" / "tools" / "schema.json")
