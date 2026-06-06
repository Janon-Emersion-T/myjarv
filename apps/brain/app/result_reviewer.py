from datetime import UTC, datetime

from app.schemas import AgentExecutionResponse, ReviewResult


class ResultReviewer:
    def review(self, task: dict, response: AgentExecutionResponse) -> ReviewResult:
        findings: list[str] = []
        score = 100

        if not response.deliverables:
            findings.append("Execution produced no deliverables.")
            score -= 30
        if not response.next_steps:
            findings.append("Execution did not provide concrete next steps.")
            score -= 15
        if task["approval_level"] != "LOW" and not response.escalations:
            findings.append("Approval-sensitive task should mention escalation or approval context.")
            score -= 10
        if task["supporting_agents"] and not response.collaborators:
            findings.append("Task planned with supporting agents but execution omitted collaborators.")
            score -= 10
        if task.get("supporting_agents") and response.contribution_count < len(task["supporting_agents"]) + 1:
            findings.append("Collaboration session did not capture all expected agent contributions.")
            score -= 15
        if task.get("routing", {}).get("review_chain") and not response.review_chain_results:
            findings.append("Review chain was planned but no collaborative review results were captured.")
            score -= 10

        verdict = "approved"
        recommended_status = "completed"
        if response.status == "blocked":
            verdict = "blocked"
            recommended_status = "failed"
            score = min(score, 45)
        elif score < 70:
            verdict = "needs_revision"
            recommended_status = "failed"

        return ReviewResult(
            reviewer="Jarvis",
            score=max(score, 0),
            verdict=verdict,
            findings=findings,
            recommended_status=recommended_status,
            created_at=datetime.now(UTC),
        )


result_reviewer = ResultReviewer()
