from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from app.agents.registry import get_agent_by_name
from app.audit_logger import audit_logger
from app.collaboration.bus import collaboration_bus
from app.collaboration.protocol import collaboration_protocol
from app.collaboration.store import collaboration_store
from app.knowledge.loader import knowledge_loader
from app.memory import memory_store


class CollaborationEngine:
    def plan(self, task: dict[str, Any], mode: str = "simulation") -> dict[str, Any]:
        routing = task.get("routing") or {}
        strategy = routing.get("execution_strategy", "single")
        participants = [task["selected_agent"]["name"], *[agent["name"] for agent in task.get("supporting_agents", [])]]
        reviewers = list(dict.fromkeys(routing.get("review_chain", [])))
        fallback_agents = [routing.get("fallback_agent")] if routing.get("fallback_agent") else []
        fallback_agents.extend(
            agent.fallback_agent
            for agent in [get_agent_by_name(name) for name in participants if name]
            if agent.fallback_agent and agent.fallback_agent not in participants
        )
        fallback_agents = list(dict.fromkeys([agent for agent in fallback_agents if agent]))
        workspace = self._build_workspace(task, participants, reviewers)
        now = collaboration_store.now()
        session = {
            "id": collaboration_store.next_id(),
            "task_id": task["id"],
            "mode": mode,
            "strategy": strategy,
            "coordinator": "Jarvis",
            "primary_agent": task["selected_agent"]["name"],
            "participants": participants,
            "reviewers": reviewers,
            "fallback_agents": fallback_agents,
            "approval_required": task["approval_level"],
            "status": "planned" if mode == "simulation" else "running",
            "shared_workspace": workspace,
            "analytics": {
                "participant_count": len(participants),
                "reviewer_count": len(reviewers),
                "authority_checks_passed": True,
                "knowledge_reference_count": len(workspace["knowledge"]),
                "memory_reference_count": len(workspace["memory_refs"]),
            },
            "created_at": now,
            "updated_at": now,
        }
        collaboration_store.create_session(session)
        self._seed_planning_events(session, task)
        return collaboration_store.get_session(session["id"])

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        session = self.plan(task, mode="execution")
        session_id = session["id"]
        contributions: list[dict[str, Any]] = []
        executor = ThreadPoolExecutor(max_workers=min(4, max(1, len(session["participants"]))))
        try:
            if session["strategy"] == "parallel" and len(session["participants"]) > 1:
                futures = [executor.submit(self._contribute, task, session, agent, "execution") for agent in session["participants"]]
                for future in futures:
                    contributions.append(future.result())
            else:
                for agent in session["participants"]:
                    contributions.append(self._contribute(task, session, agent, "execution"))
        finally:
            executor.shutdown(wait=True)

        review_results = []
        for reviewer in session["reviewers"]:
            review_results.append(self._review(task, session, reviewer, contributions))

        analytics = self._build_analytics(session, contributions, review_results)
        shared_workspace = session["shared_workspace"] | {
            "latest_contribution_agents": [item["agent"] for item in contributions],
            "review_summaries": review_results,
        }
        final_status = "completed" if all(item["quality_score"] >= 70 for item in contributions) else "blocked"
        collaboration_store.update_session(session_id, status=final_status, analytics=analytics, shared_workspace=shared_workspace)
        collaboration_bus.publish_event(
            {
                "id": collaboration_store.next_id(),
                "session_id": session_id,
                "task_id": task["id"],
                "event_type": "session_completed",
                "actor": "Jarvis",
                "stage": "finalize",
                "message": f"Collaboration session finished with status {final_status}.",
                "payload": {"contribution_count": len(contributions), "review_count": len(review_results)},
                "created_at": collaboration_store.now(),
            }
        )
        audit_logger.record(
            "collaboration_completed",
            "Completed collaboration session.",
            {"session_id": session_id, "task_id": task["id"], "status": final_status},
        )
        return collaboration_store.get_session(session_id)

    def replay(self, session_id: str) -> dict[str, Any]:
        session = collaboration_store.get_session(session_id)
        task = {
            "id": session["task_id"],
            "selected_agent": {"name": session["primary_agent"], "role": get_agent_by_name(session["primary_agent"]).role},
            "supporting_agents": [{"name": name} for name in session["participants"] if name != session["primary_agent"]],
            "approval_level": session["approval_required"],
            "routing": {"execution_strategy": session["strategy"], "review_chain": session["reviewers"], "fallback_agent": session["fallback_agents"][0] if session["fallback_agents"] else "Jarvis"},
            "message": session["shared_workspace"].get("task_message", "Replay task"),
            "intent_category": session["shared_workspace"].get("intent_category", "general"),
            "metadata": {},
        }
        return self.plan(task, mode="replay")

    def _seed_planning_events(self, session: dict[str, Any], task: dict[str, Any]) -> None:
        session_id = session["id"]
        task_id = task["id"]
        collaboration_bus.publish_event(
            {
                "id": collaboration_store.next_id(),
                "session_id": session_id,
                "task_id": task_id,
                "event_type": "session_started",
                "actor": "Jarvis",
                "stage": "intake",
                "message": f"Jarvis opened collaboration session for task {task_id}.",
                "payload": {"strategy": session["strategy"], "participants": session["participants"]},
                "created_at": collaboration_store.now(),
            }
        )
        for participant in session["participants"]:
            message = collaboration_protocol.instruction("Jarvis", participant, task["message"], "execution")
            collaboration_bus.publish_message(
                {
                    "id": collaboration_store.next_id(),
                    "session_id": session_id,
                    "task_id": task_id,
                    "sender": "Jarvis",
                    "recipient": participant,
                    "kind": "instruction",
                    "content": message,
                    "related_stage": "execution",
                    "created_at": collaboration_store.now(),
                }
            )
        for reviewer in session["reviewers"]:
            collaboration_bus.publish_message(
                {
                    "id": collaboration_store.next_id(),
                    "session_id": session_id,
                    "task_id": task_id,
                    "sender": "Jarvis",
                    "recipient": reviewer,
                    "kind": "review",
                    "content": collaboration_protocol.review("Jarvis", reviewer, task["message"]),
                    "related_stage": "review",
                    "created_at": collaboration_store.now(),
                }
            )
        for memory_ref in session["shared_workspace"]["memory_refs"][:3]:
            for participant in session["participants"][:2]:
                collaboration_bus.publish_message(
                    {
                        "id": collaboration_store.next_id(),
                        "session_id": session_id,
                        "task_id": task_id,
                        "sender": "Jarvis",
                        "recipient": participant,
                        "kind": "memory_ref",
                        "content": collaboration_protocol.memory_ref("Jarvis", participant, memory_ref["scope"], memory_ref["key"]),
                        "related_stage": "planning",
                        "created_at": collaboration_store.now(),
                    }
                )
        for knowledge_ref in session["shared_workspace"]["knowledge"][:3]:
            for participant in session["participants"][:2]:
                collaboration_bus.publish_message(
                    {
                        "id": collaboration_store.next_id(),
                        "session_id": session_id,
                        "task_id": task_id,
                        "sender": "Jarvis",
                        "recipient": participant,
                        "kind": "knowledge_ref",
                        "content": collaboration_protocol.knowledge_ref("Jarvis", participant, knowledge_ref["path"]),
                        "related_stage": "planning",
                        "created_at": collaboration_store.now(),
                    }
                )

    def _contribute(self, task: dict[str, Any], session: dict[str, Any], agent_name: str, stage: str) -> dict[str, Any]:
        agent = get_agent_by_name(agent_name)
        now = collaboration_store.now()
        fallback_used = None
        deliverables = [
            f"{agent.name} addressed the {task['intent_category']} workstream.",
            f"Authority scope respected: {agent.authority_scope}.",
        ]
        if task["routing"].get("framework_hints"):
            deliverables.append(f"Framework focus: {', '.join(task['routing']['framework_hints'])}.")
        if task["routing"].get("tool_matches"):
            deliverables.append(f"Tool focus: {', '.join(task['routing']['tool_matches'])}.")
        if agent.approval_level == "CRITICAL" and task["approval_level"] in {"LOW", "MEDIUM"}:
            fallback_used = agent.fallback_agent or session["fallback_agents"][0] if session["fallback_agents"] else None
        quality_score = self._quality_score(agent, task)
        contribution = {
            "id": collaboration_store.next_id(),
            "session_id": session["id"],
            "task_id": task["id"],
            "agent": agent.name,
            "role": agent.role,
            "stage": stage,
            "status": "completed" if quality_score >= 70 else "blocked",
            "summary": f"{agent.name} contributed specialist guidance for '{task['message']}'.",
            "deliverables": deliverables,
            "quality_score": quality_score,
            "references": [item["path"] for item in session["shared_workspace"]["knowledge"][:2]],
            "fallback_used": fallback_used,
            "created_at": now,
            "updated_at": now,
        }
        collaboration_bus.publish_contribution(contribution)
        collaboration_bus.publish_event(
            {
                "id": collaboration_store.next_id(),
                "session_id": session["id"],
                "task_id": task["id"],
                "event_type": "agent_contributed",
                "actor": agent.name,
                "stage": stage,
                "message": f"{agent.name} completed a collaboration contribution.",
                "payload": {"quality_score": quality_score, "fallback_used": fallback_used},
                "created_at": collaboration_store.now(),
            }
        )
        return contribution

    def _review(self, task: dict[str, Any], session: dict[str, Any], reviewer_name: str, contributions: list[dict[str, Any]]) -> str:
        review_focus = []
        lowered = {contrib["agent"].lower() for contrib in contributions}
        if "neil" in lowered:
            review_focus.append("SEO")
        if "lawrence" in lowered or task["intent_category"] == "legal":
            review_focus.append("legal")
        if "morgan" in lowered or task["intent_category"] == "finance":
            review_focus.append("finance")
        if "sentinel" in lowered or task["risk_level"] in {"HIGH", "CRITICAL"}:
            review_focus.append("security")
        if task["intent_category"] == "development":
            review_focus.append("architecture")
            review_focus.append("code-review")
            review_focus.append("documentation")
            review_focus.append("qa")
        summary = f"{reviewer_name} reviewed collaboration outputs for {', '.join(dict.fromkeys(review_focus)) or 'general quality'}."
        collaboration_bus.publish_event(
            {
                "id": collaboration_store.next_id(),
                "session_id": session["id"],
                "task_id": task["id"],
                "event_type": "review_completed",
                "actor": reviewer_name,
                "stage": "review",
                "message": summary,
                "payload": {"focus": review_focus, "contribution_count": len(contributions)},
                "created_at": collaboration_store.now(),
            }
        )
        return summary

    def _build_workspace(self, task: dict[str, Any], participants: list[str], reviewers: list[str]) -> dict[str, Any]:
        memory_refs = []
        for scope in ("company", "project", "client", "decision", "agent"):
            memory_refs.extend(memory_store.list(scope=scope, limit=2))
        knowledge = knowledge_loader.retrieve_relevant(task["message"], limit=6)
        return {
            "task_message": task["message"],
            "intent_category": task["intent_category"],
            "participants": participants,
            "reviewers": reviewers,
            "memory_refs": memory_refs[:10],
            "knowledge": knowledge,
            "route_trace_id": task.get("routing", {}).get("trace_id"),
            "shared_files": [],
            "timeline_hint": task.get("routing", {}).get("route_map", {}),
        }

    def _quality_score(self, agent: Any, task: dict[str, Any]) -> int:
        score = 80
        if task["intent_category"] in {domain for domain in agent.knowledge_domains}:
            score += 8
        if task["approval_level"] == "CRITICAL":
            score -= 5
        if task.get("routing", {}).get("framework_hints") and any(
            hint in agent.knowledge_domains or hint in {tool.lower() for tool in agent.tools}
            for hint in task["routing"]["framework_hints"]
        ):
            score += 7
        return max(65, min(score, 98))

    def _build_analytics(self, session: dict[str, Any], contributions: list[dict[str, Any]], review_results: list[str]) -> dict[str, Any]:
        stage_counts: dict[str, int] = {}
        for contribution in contributions:
            stage_counts[contribution["stage"]] = stage_counts.get(contribution["stage"], 0) + 1
        return {
            "participant_count": len(session["participants"]),
            "reviewer_count": len(session["reviewers"]),
            "contribution_count": len(contributions),
            "average_quality_score": round(sum(item["quality_score"] for item in contributions) / len(contributions), 2),
            "stage_counts": stage_counts,
            "review_count": len(review_results),
            "asynchronous_execution": session["strategy"] == "parallel",
            "realtime_tracking_enabled": True,
        }


collaboration_engine = CollaborationEngine()
