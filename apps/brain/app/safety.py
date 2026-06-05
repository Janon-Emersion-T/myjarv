from app.approval_gate import LEVEL_ORDER


def is_execution_allowed(task: dict) -> bool:
    if task["approval_level"] == "LOW":
        return True
    return task["status"] == "approved"


def should_retry(task: dict, max_retries: int = 1) -> bool:
    return task.get("retry_count", 0) < max_retries and LEVEL_ORDER[task["risk_level"]] <= LEVEL_ORDER["HIGH"]
