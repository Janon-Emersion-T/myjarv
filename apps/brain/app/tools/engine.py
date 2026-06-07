from __future__ import annotations

import os
import subprocess
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path
from typing import Any, Callable

from app.agents.registry import get_agent_by_name
from app.config import ROOT_DIR
from app.tools.registry import tool_registry
from app.tools.store import tool_execution_store


WHITELISTED_COMMAND_PREFIXES = [
    "pwd",
    "ls",
    "find",
    "rg",
    "cat",
    "sed",
    "git status",
    "git diff",
    "git log",
    "python3 --version",
    "npm run build",
    "cargo check",
]
BLACKLISTED_COMMAND_FRAGMENTS = ["rm -rf", "shutdown", "reboot", "mkfs", "dd ", "curl | sh", ">:(", "chmod 777", "git push", "git reset --hard"]


class ToolExecutionEngine:
    def __init__(self) -> None:
        self._history_window: dict[str, deque[float]] = {}
        self._queued_jobs: list[dict[str, Any]] = []
        self.handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "file_read": self._file_read,
            "file_write": self._file_write,
            "terminal_command_tool": self._terminal_command,
            "safe_shell_plan": self._safe_shell_plan,
            "git_status": self._git_status,
            "project_scanner": self._project_scanner,
            "documentation_generator": self._documentation_generator,
            "code_reviewer": self._code_reviewer,
            "website_project_planner": self._website_project_planner,
            "seo_audit_tool": self._seo_audit_tool,
            "proposal_generator": self._proposal_generator,
            "code_generator": self._code_generator,
            "deployment_assistant": self._deployment_assistant,
            "browser_search_tool": self._browser_search_tool,
            "email_tool": self._email_tool,
            "calendar_tool": self._calendar_tool,
            "whatsapp_tool": self._whatsapp_tool,
            "invoice_tool": self._invoice_tool,
            "github_integration_tool": self._github_integration_tool,
        }

    def execute(
        self,
        *,
        tool_name: str,
        input_payload: dict[str, Any],
        actor: str = "Jarvis",
        agent_name: str | None = None,
        task_id: str | None = None,
        approved: bool = False,
        async_mode: bool = False,
    ) -> dict[str, Any]:
        tool = tool_registry.get_tool(tool_name)
        self._validate_input(tool, input_payload)
        self._check_rate_limit(tool)
        self._check_permissions(tool, agent_name)
        if tool["approval_requirement"] != "LOW" and not approved:
            return tool_execution_store.record(
                tool_name=tool["name"],
                actor=actor,
                agent_name=agent_name,
                task_id=task_id,
                status="blocked",
                mode=tool["mode"],
                risk_level=tool["risk_level"],
                approval_requirement=tool["approval_requirement"],
                async_mode=async_mode,
                queued=False,
                input_payload=input_payload,
                output_payload={"message": f"{tool['name']} requires {tool['approval_requirement']} approval."},
                error=None,
                duration_ms=0,
            )
        if async_mode and tool.get("queue_supported"):
            queued = {
                "tool_name": tool["name"],
                "input_payload": input_payload,
                "actor": actor,
                "agent_name": agent_name,
                "task_id": task_id,
                "approved": approved,
            }
            self._queued_jobs.append(queued)
            return tool_execution_store.record(
                tool_name=tool["name"],
                actor=actor,
                agent_name=agent_name,
                task_id=task_id,
                status="queued",
                mode=tool["mode"],
                risk_level=tool["risk_level"],
                approval_requirement=tool["approval_requirement"],
                async_mode=True,
                queued=True,
                input_payload=input_payload,
                output_payload={"message": "Tool execution queued."},
                error=None,
                duration_ms=0,
            )
        return self._run(tool, input_payload, actor, agent_name, task_id, approved, async_mode)

    def process_queue(self, limit: int = 10) -> dict[str, Any]:
        processed = []
        for _ in range(min(limit, len(self._queued_jobs))):
            job = self._queued_jobs.pop(0)
            processed.append(
                self._run(
                    tool_registry.get_tool(job["tool_name"]),
                    job["input_payload"],
                    job["actor"],
                    job["agent_name"],
                    job["task_id"],
                    job["approved"],
                    True,
                )
            )
        return {"processed": len(processed), "executions": processed}

    def execute_workflow(self, steps: list[dict[str, Any]], actor: str = "Jarvis", approved: bool = False) -> dict[str, Any]:
        results = []
        for step in steps:
            results.append(
                self.execute(
                    tool_name=step["tool_name"],
                    input_payload=step.get("input", {}),
                    actor=actor,
                    agent_name=step.get("agent_name"),
                    task_id=step.get("task_id"),
                    approved=approved or step.get("approved", False),
                    async_mode=step.get("async_mode", False),
                )
            )
        return {"steps": results, "completed": sum(1 for item in results if item["status"] in {"completed", "queued"}), "total": len(results)}

    def replay(self, execution_id: str, approved: bool = False) -> dict[str, Any]:
        execution = tool_execution_store.get(execution_id)
        return self.execute(
            tool_name=execution["tool_name"],
            input_payload=execution["input"],
            actor=execution["actor"],
            agent_name=execution["agent_name"],
            task_id=execution["task_id"],
            approved=approved,
            async_mode=False,
        )

    def prometheus_metrics(self) -> str:
        metrics = tool_execution_store.analytics()
        lines = [
            "# HELP jarvis_tools_total Total recorded tool executions.",
            "# TYPE jarvis_tools_total gauge",
            f"jarvis_tools_total {metrics['total_executions']}",
            "# HELP jarvis_tool_average_duration_ms Average tool execution duration in milliseconds.",
            "# TYPE jarvis_tool_average_duration_ms gauge",
            f"jarvis_tool_average_duration_ms {metrics['average_duration_ms']}",
        ]
        for tool_name, count in metrics["by_tool"].items():
            lines.append(f'jarvis_tool_executions_by_tool{{tool="{tool_name}"}} {count}')
        for status, count in metrics["by_status"].items():
            lines.append(f'jarvis_tool_executions_by_status{{status="{status}"}} {count}')
        return "\n".join(lines)

    def _run(
        self,
        tool: dict[str, Any],
        input_payload: dict[str, Any],
        actor: str,
        agent_name: str | None,
        task_id: str | None,
        approved: bool,
        async_mode: bool,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        handler = self.handlers.get(tool["name"])
        if handler is None:
            return tool_execution_store.record(
                tool_name=tool["name"],
                actor=actor,
                agent_name=agent_name,
                task_id=task_id,
                status="failed",
                mode=tool["mode"],
                risk_level=tool["risk_level"],
                approval_requirement=tool["approval_requirement"],
                async_mode=async_mode,
                queued=False,
                input_payload=input_payload,
                output_payload=None,
                error="No execution handler is registered for this tool.",
                duration_ms=0,
            )
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(handler, input_payload)
                output = future.result(timeout=tool["timeout_seconds"])
            status = "completed"
            error = None
        except FutureTimeout:
            output = None
            status = "failed"
            error = f"Tool timed out after {tool['timeout_seconds']} seconds."
        except Exception as exc:  # noqa: BLE001
            output = None
            status = "failed"
            error = str(exc)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        if status == "failed" and tool.get("fallback_tool"):
            output = {
                "message": f"{tool['name']} failed; use fallback {tool['fallback_tool']}.",
                "fallback_tool": tool["fallback_tool"],
            }
            status = "fallback"
            error = error
        return tool_execution_store.record(
            tool_name=tool["name"],
            actor=actor,
            agent_name=agent_name,
            task_id=task_id,
            status=status,
            mode=tool["mode"],
            risk_level=tool["risk_level"],
            approval_requirement=tool["approval_requirement"],
            async_mode=async_mode,
            queued=False,
            input_payload=input_payload,
            output_payload=output,
            error=error,
            duration_ms=duration_ms,
        )

    def _validate_input(self, tool: dict[str, Any], payload: dict[str, Any]) -> None:
        for key, expected in tool["input_schema"].items():
            if key not in payload:
                raise ValueError(f"Missing required input: {key}")
            if expected == "string" and not isinstance(payload[key], str):
                raise ValueError(f"Expected string for {key}")
            if expected == "array" and not isinstance(payload[key], list):
                raise ValueError(f"Expected array for {key}")

    def _check_permissions(self, tool: dict[str, Any], agent_name: str | None) -> None:
        if not agent_name:
            return
        agent = get_agent_by_name(agent_name)
        compatible = tool_registry.compatible_tools_for_agent(agent.name, agent.tools)
        compatible_names = {item["name"] for item in compatible}
        if tool["name"] not in compatible_names and tool["approval_requirement"] != "LOW":
            raise ValueError(f"Agent {agent.name} is not approved to use tool {tool['name']}.")

    def _check_rate_limit(self, tool: dict[str, Any]) -> None:
        window = self._history_window.setdefault(tool["name"], deque())
        now = time.time()
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= tool["rate_limit_per_minute"]:
            raise ValueError(f"Rate limit exceeded for tool {tool['name']}.")
        window.append(now)

    def _safe_shell_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        goal = payload["goal"].strip()
        return {
            "plan": "\n".join(
                [
                    f"Goal: {goal}",
                    "1. Inspect the workspace and confirm the current state.",
                    "2. Choose the least-destructive command sequence first.",
                    "3. Validate outputs before any write or deploy action.",
                ]
            )
        }

    def _terminal_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        command = payload["command"].strip()
        lowered = command.lower()
        if any(fragment in lowered for fragment in BLACKLISTED_COMMAND_FRAGMENTS):
            raise ValueError("Dangerous command blocked by blacklist.")
        if not any(lowered == prefix or lowered.startswith(f"{prefix} ") for prefix in WHITELISTED_COMMAND_PREFIXES):
            raise ValueError("Command is not in the shell whitelist.")
        cwd = Path(payload.get("cwd") or ROOT_DIR).resolve()
        completed = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True, timeout=8, check=False)
        return {"stdout": completed.stdout.strip(), "stderr": completed.stderr.strip(), "returncode": completed.returncode}

    def _file_read(self, payload: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_local_path(payload["path"])
        return {"content": path.read_text(encoding="utf-8")}

    def _file_write(self, payload: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_local_path(payload["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload["content"], encoding="utf-8")
        return {"written": True, "path": str(path)}

    def _git_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_local_path(payload["path"])
        completed = subprocess.run(["git", "-C", str(path), "status", "--short"], capture_output=True, text=True, check=False, timeout=5)
        return {"summary": completed.stdout.strip() or "Working tree clean."}

    def _project_scanner(self, payload: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve_local_path(payload["path"])
        entries = sorted(item.name for item in path.iterdir())[:20]
        report = f"Scanned {path}. Top-level entries: {', '.join(entries)}"
        return {"report": report}

    def _documentation_generator(self, payload: dict[str, Any]) -> dict[str, Any]:
        topic = payload["topic"].strip()
        return {"document": f"# {topic}\n\n## Purpose\n\nDraft documentation for {topic}.\n\n## Notes\n\n- Confirm scope.\n- Add implementation details.\n- Review before release.\n"}

    def _code_reviewer(self, payload: dict[str, Any]) -> dict[str, Any]:
        findings = []
        for path_text in payload["paths"][:10]:
            path = self._resolve_local_path(path_text)
            findings.append({"path": str(path), "risk": "review", "note": "Manual review still required for behavior and tests."})
        return {"findings": findings}

    def _website_project_planner(self, payload: dict[str, Any]) -> dict[str, Any]:
        brief = payload["brief"].strip()
        return {"plan": f"Website plan for: {brief}\n1. Discovery\n2. Sitemap and content\n3. UI implementation\n4. QA and launch"}

    def _seo_audit_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        target = payload["target"].strip()
        return {"checklist": [f"Validate metadata for {target}", "Check headings", "Review internal links", "Audit page speed", "Confirm search-console readiness"]}

    def _proposal_generator(self, payload: dict[str, Any]) -> dict[str, Any]:
        brief = payload["brief"].strip()
        return {"proposal": f"Client Proposal\n\nProblem\n{brief}\n\nScope\n- Discovery\n- Delivery\n- Review\n\nCommercial Terms\n- Confirm timeline and pricing approval.\n"}

    def _code_generator(self, payload: dict[str, Any]) -> dict[str, Any]:
        goal = payload["goal"].strip()
        return {"artifact": f"// Draft generated artifact\n// Goal: {goal}\n\nfunction placeholder() {{\n  return \"Implement {goal}\";\n}}\n"}

    def _deployment_assistant(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"plan": f"Deployment plan for {payload['environment']}: {payload['goal']}\n- Validate build\n- Review backup and rollback\n- Confirm approval gate\n- Execute controlled release"}

    def _browser_search_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"plan": f"Browser research plan for {payload['goal']}\n- Define trusted sources\n- Search targeted domains\n- Capture findings and citations"}

    def _email_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"draft": f"To: {payload['recipient']}\nSubject: {payload['subject']}\n\n{payload['message']}"}

    def _calendar_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"plan": f"Schedule '{payload['event']}' on {payload['date']} after confirming participants and approval context."}

    def _whatsapp_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"draft": f"WhatsApp draft to {payload['recipient']}: {payload['message']}"}

    def _invoice_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        lines = payload["items"]
        return {"document": f"Invoice draft for {payload['client']} with {len(lines)} line item(s)."}

    def _github_integration_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"plan": f"GitHub action plan for {payload['repository']}: {payload['action']}"}

    def _resolve_local_path(self, path_text: str) -> Path:
        path = Path(path_text)
        resolved = path if path.is_absolute() else (ROOT_DIR / path)
        resolved = resolved.resolve()
        if not str(resolved).startswith(str(ROOT_DIR)):
            raise ValueError("Path escapes the workspace root.")
        return resolved


tool_execution_engine = ToolExecutionEngine()
