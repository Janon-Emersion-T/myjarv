from collections import deque


class TaskQueue:
    def __init__(self) -> None:
        self._queue: deque[str] = deque()

    def enqueue(self, task_id: str) -> None:
        if task_id not in self._queue:
            self._queue.append(task_id)

    def dequeue(self) -> str | None:
        if not self._queue:
            return None
        return self._queue.popleft()

    def list_pending(self) -> list[str]:
        return list(self._queue)

    def remove(self, task_id: str) -> None:
        self._queue = deque(item for item in self._queue if item != task_id)


task_queue = TaskQueue()
