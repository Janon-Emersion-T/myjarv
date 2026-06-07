from __future__ import annotations

import asyncio


class ApprovalBus:
    def __init__(self) -> None:
        self._queues: list[asyncio.Queue] = []

    def publish(self, event_type: str, payload: dict) -> None:
        message = {"type": event_type, "payload": payload}
        for queue in list(self._queues):
            queue.put_nowait(message)

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._queues.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._queues = [item for item in self._queues if item is not queue]


approval_bus = ApprovalBus()
