from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from app.collaboration.store import collaboration_store


class CollaborationBus:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def publish_event(self, payload: dict[str, Any]) -> None:
        collaboration_store.add_event(payload)
        self._broadcast(payload["session_id"], {"type": "event", "payload": payload})

    def publish_message(self, payload: dict[str, Any]) -> None:
        collaboration_store.add_message(payload)
        self._broadcast(payload["session_id"], {"type": "message", "payload": payload})

    def publish_contribution(self, payload: dict[str, Any]) -> None:
        collaboration_store.add_contribution(payload)
        self._broadcast(payload["session_id"], {"type": "contribution", "payload": payload})

    def subscribe(self, session_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._queues[session_id].append(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        listeners = self._queues.get(session_id, [])
        self._queues[session_id] = [item for item in listeners if item is not queue]

    def _broadcast(self, session_id: str, message: dict[str, Any]) -> None:
        for queue in self._queues.get(session_id, []):
            queue.put_nowait(message)


collaboration_bus = CollaborationBus()
