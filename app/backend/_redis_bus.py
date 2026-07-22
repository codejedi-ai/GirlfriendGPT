"""Real Redis Streams ``QueueBus`` implementation.

Backed by ``redis.asyncio``. Public surface matches ``QueueBus`` in
``bus.py`` exactly, so the factory in ``factory.py`` can swap this in
without any call site changing.

Streams + consumer-group semantics:

- ``publish(stream, data)`` -> XADD
- ``consume(stream, group, consumer)`` -> XREADGROUP loop; auto-creates
  the consumer group with MKSTREAM the first time so the worker can boot
  before any producer has published.
- ``ack(stream, group, message_id)`` -> XACK

If the ``redis`` package isn't importable (sandbox case), ``REAL_AVAILABLE``
stays ``False`` and the factory falls back to ``InMemoryQueueBus``.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator

from .bus import QueueMessage


try:  # pragma: no cover - import availability is environment-dependent
    import redis.asyncio as redis_asyncio  # type: ignore

    REAL_AVAILABLE = True
except Exception:  # noqa: BLE001
    redis_asyncio = None  # type: ignore[assignment]
    REAL_AVAILABLE = False


class RedisStreamBus:
    """Redis Streams implementation of the QueueBus protocol."""

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        *,
        block_ms: int = 1000,
        max_payload_bytes: int = 1_000_000,
    ) -> None:
        if not REAL_AVAILABLE:
            raise RuntimeError(
                "redis package not installed; install 'redis>=5.0' or "
                "use InMemoryQueueBus"
            )
        self._url = url
        self._block_ms = block_ms
        self._max_payload_bytes = max_payload_bytes
        self._client = redis_asyncio.from_url(url, decode_responses=True)
        self._groups_ensured: set[tuple[str, str]] = set()
        self._closed = False

    async def _ensure_group(self, stream: str, group: str) -> None:
        key = (stream, group)
        if key in self._groups_ensured:
            return
        try:
            # MKSTREAM creates the stream if it doesn't exist yet, so the
            # consumer can start before the producer.
            await self._client.xgroup_create(
                name=stream, groupname=group, id="0", mkstream=True
            )
        except Exception as e:  # BUSYGROUP means the group already exists.
            if "BUSYGROUP" not in str(e):
                raise
        self._groups_ensured.add(key)

    async def publish(self, stream: str, data: dict[str, Any]) -> str:
        payload = json.dumps(data, sort_keys=True)
        if len(payload) > self._max_payload_bytes:
            raise ValueError(
                f"payload too large for stream {stream}: {len(payload)} bytes"
            )
        return await self._client.xadd(stream, {"data": payload})

    async def consume(
        self, stream: str, group: str, consumer: str
    ) -> AsyncIterator[QueueMessage]:
        await self._ensure_group(stream, group)
        while not self._closed:
            try:
                resp = await self._client.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams={stream: ">"},
                    count=1,
                    block=self._block_ms,
                )
            except Exception as exc:
                # If the stream/group was deleted out from under us (e.g. a
                # reset wiped the streams), recreate the group and carry on —
                # a worker must survive its stream being cleared.
                if "NOGROUP" in str(exc):
                    self._groups_ensured.discard((stream, group))
                    try:
                        await self._ensure_group(stream, group)
                    except Exception:
                        await asyncio.sleep(0.1)
                    continue
                # Network blip — let the caller retry/log via the higher level.
                await asyncio.sleep(0.1)
                continue
            if not resp:
                # Block timeout: yield control and re-poll.
                await asyncio.sleep(0)
                continue
            for _stream_name, entries in resp:
                for entry_id, fields in entries:
                    try:
                        data = json.loads(fields["data"])
                    except Exception:
                        # Bad message - ack and skip.
                        await self.ack(stream, group, entry_id)
                        continue
                    yield QueueMessage(
                        stream=stream, message_id=entry_id, data=data
                    )

    async def ack(self, stream: str, group: str, message_id: str) -> None:
        await self._client.xack(stream, group, message_id)

    async def length(self, stream: str) -> int:
        try:
            return int(await self._client.xlen(stream))
        except Exception:
            return 0

    async def close(self) -> None:
        self._closed = True
        try:
            await self._client.aclose()
        except Exception:
            pass
