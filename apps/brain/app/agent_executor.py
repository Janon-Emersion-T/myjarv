from app.agent_response import build_agent_response
from app.collaboration import collaboration_engine
from app.context_builder import context_builder
from app.exceptions import TaskExecutionError
from app.knowledge_loader import load_relevant_knowledge
from app.tool_loader import load_tools_for_task


class AgentExecutor:
    def execute(self, task: dict):
        context = context_builder.build(task)
        selected_agent = task["selected_agent"]
        collaborators = [agent["name"] for agent in task.get("supporting_agents", [])]
        knowledge = load_relevant_knowledge(task["message"], limit=4)
        tools = load_tools_for_task(task)
        collaboration_session = collaboration_engine.execute(task)
        contributions = collaboration_session["contributions"]
        review_chain_results = [
            event["message"] for event in collaboration_session["events"] if event["event_type"] == "review_completed"
        ]

        if not selected_agent:
            raise TaskExecutionError("No selected agent is attached to the task.")

        summary = (
            f"{selected_agent['name']} handled the {task['intent_category']} request by preparing a structured plan for "
            f"'{task['message']}'. The response is grounded in company context, relevant knowledge, collaborative specialist input, and approval-aware next steps."
        )
        deliverables = [
            f"Primary owner: {selected_agent['name']} ({selected_agent['role']}).",
            f"Intent category: {task['intent_category']}.",
            f"Priority {task['priority']} with risk {task['risk_level']} and approval level {task['approval_level']}.",
            f"Collaboration session: {collaboration_session['id']} using {collaboration_session['strategy']} execution.",
        ]
        next_steps = [
            "Review the scoped plan and confirm any unresolved assumptions.",
            "Use the suggested tools and knowledge sources before external execution.",
            "Escalate or approve the task before performing risky, destructive, or client-facing actions.",
        ]
        escalations = []
        if task["approval_level"] != "LOW":
            escalations.append(
                f"Execution remains approval-aware; final external or destructive actions require {task['approval_level']} approval."
            )
        if collaborators:
            escalations.append(f"Collaborate with supporting agents: {', '.join(collaborators)}.")
        if collaboration_session["fallback_agents"]:
            escalations.append(f"Fallback agents available: {', '.join(collaboration_session['fallback_agents'])}.")

        return build_agent_response(
            primary_agent=selected_agent["name"],
            collaborators=collaborators,
            collaboration_session_id=collaboration_session["id"],
            collaboration_strategy=collaboration_session["strategy"],
            contributions=contributions,
            contribution_count=len(contributions),
            collaboration_timeline=collaboration_session["events"],
            review_chain_results=review_chain_results,
            summary=summary,
            deliverables=deliverables,
            next_steps=next_steps,
            escalations=escalations,
            tool_plans=[f"Consider tool `{tool['name']}` in `{tool['mode']}` mode." for tool in tools[:4]],
            knowledge_used=[entry["path"] for entry in knowledge],
            context_notes=[
                f"Personality stance: {context['personality']['stance']}",
                f"Memory items considered: {len(context['memory'])}",
                f"Knowledge items considered: {len(context['knowledge'])}",
            ],
            status="completed",
        )

agent_executor = AgentExecutor()
