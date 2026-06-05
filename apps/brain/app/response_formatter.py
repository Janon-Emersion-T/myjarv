from app.schemas import AgentExecutionResponse, ReviewResult


class ResponseFormatter:
    def format_execution(self, response: AgentExecutionResponse) -> dict:
        return response.model_dump(mode="json")

    def parse_execution(self, payload: dict) -> AgentExecutionResponse:
        return AgentExecutionResponse(**payload)

    def format_review(self, review: ReviewResult) -> dict:
        return review.model_dump(mode="json")


response_formatter = ResponseFormatter()
