class JarvisBrainError(Exception):
    """Base exception for Jarvis brain operations."""


class TaskStateError(JarvisBrainError):
    """Raised when a task is not in a valid state for the requested operation."""


class ApprovalRequiredError(JarvisBrainError):
    """Raised when an action cannot continue until approval is granted."""


class TaskExecutionError(JarvisBrainError):
    """Raised when task execution fails after retries or validation."""
