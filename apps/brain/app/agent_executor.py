from app.agent_response import build_agent_response
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

        if not selected_agent:
            raise TaskExecutionError("No selected agent is attached to the task.")

        summary = (
            f"{selected_agent['name']} handled the {task['intent_category']} request by preparing a structured plan for "
            f"'{task['message']}'. The response is grounded in company context, relevant knowledge, and approval-aware next steps."
        )
        deliverables = [
            f"Primary owner: {selected_agent['name']} ({selected_agent['role']}).",
            f"Intent category: {task['intent_category']}.",
            f"Priority {task['priority']} with risk {task['risk_level']} and approval level {task['approval_level']}.",
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

        return build_agent_response(
            primary_agent=selected_agent["name"],
            collaborators=collaborators,
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
