"""Queue bus — the spine that every channel adapter and agent talks to.

v0.1 ships ``InMemoryQueueBus`` so the whole harness is testable in-process
without standing up Redis. The ``QueueBus`` protocol is shaped to match
Redis Streams semantics (consumer groups, XADD, XREADGROUP, XACK) so the
``RedisStreamBus`` impl drops in without changing call sites.

Streams used by the harness (see design §6):

    agents:inbound       — all channel-adapter inbound messages
    agents:replies       — all agent outbound replies
    agents:reflection    — background promotion jobs
"""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, AsyncIterator, Protocol


STREAM_INBOUND = "agents:inbound"      # channel adapter -> dispatcher agent
STREAM_TASKS = "agents:tasks"          # dispatcher -> task-specific agent
STREAM_RESULTS = "agents:results"      # task-specific agent -> dispatcher
STREAM_REPLIES = "agents:replies"      # dispatcher -> channel adapter
STREAM_REFLECTION = "agents:reflection"  # background promotion jobs


@dataclass
class QueueMessage:
    """One entry on a stream."""

    stream: str
    message_id: str
    data: dict[str, Any]


class QueueBus(Protocol):
    """Minimal Redis-Streams-shaped surface."""

    async def publish(self, stream: str, data: dict[str, Any]) -> str: ...

    async def consume(
        self, stream: str, group: str, consumer: str
    ) -> AsyncIterator[QueueMessage]: ...

    async def ack(self, stream: str, group: str, message_id: str) -> None: ...

    async def length(self, stream: str) -> int: ...


class InMemoryQueueBus:
    """In-process implementation of QueueBus.

    Per-stream FIFO queue with one pending-set per consumer-group. Calling
    ``consume`` returns an async iterator that blocks until new messages
    appear or the bus is closed. Multiple consumer groups on the same stream
    each see every message once (fan-out across groups, round-robin within
    a group is not modeled — first awaiter wins, which is fine for v0.1
    because each group has one consumer).
    """

    def __init__(self) -> None:
        self._streams: dict[str, deque[QueueMessage]] = defaultdict(deque)
        self._delivered: dict[tuple[str, str], set[str]] = defaultdict(set)
        self._cond = asyncio.Condition()
        self._counter = 0
        self._closed = False

    def _next_id(self) -> str:
        self._counter += 1
        return f"{self._counter:010d}-0"

    async def publish(self, stream: str, data: dict[str, Any]) -> str:
        async with self._cond:
            msg_id = self._next_id()
            self._streams[stream].append(
                QueueMessage(stream=stream, message_id=msg_id, data=data)
            )
            self._cond.notify_all()
            return msg_id

    async def consume(
        self, stream: str, group: str, consumer: str
    ) -> AsyncIterator[QueueMessage]:
        # consumer arg unused in v0.1 (single consumer per group) — kept for
        # protocol parity with Redis Streams' XREADGROUP signature.
        del consumer
        while True:
            next_msg: QueueMessage | None = None
            async with self._cond:
                delivered = self._delivered[(stream, group)]
                for msg in self._streams[stream]:
                    if msg.message_id not in delivered:
                        delivered.add(msg.message_id)
                        next_msg = msg
                        break
                if next_msg is None:
                    if self._closed:
                        return
                    await self._cond.wait()
            # Yield outside the lock so close() and publish() can proceed.
            if next_msg is not None:
                yield next_msg

    async def ack(self, stream: str, group: str, message_id: str) -> None:
        # No-op for v0.1 — we track delivery, not pending. When Redis Streams
        # is wired in, this becomes XACK.
        del stream, group, message_id

    async def length(self, stream: str) -> int:
        return len(self._streams[stream])

    async def close(self) -> None:
        async with self._cond:
            self._closed = True
            self._cond.notify_all()


# TODO(redis-streams): RedisStreamBus implementation.
# Same protocol; ``publish`` is XADD, ``consume`` is XREADGROUP, ``ack``
# is XACK. Stream names match the constants above. Consumer-group naming
# convention: see design §6.
