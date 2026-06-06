from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class VoiceBus:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, session_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._queues[session_id].append(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        self._queues[session_id] = [item for item in self._queues.get(session_id, []) if item is not queue]

    def publish(self, session_id: str, packet: dict[str, Any]) -> None:
        for queue in self._queues.get(session_id, []):
            queue.put_nowait(packet)


voice_bus = VoiceBus()
