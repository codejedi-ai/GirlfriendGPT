"""Tests for InMemoryQueueBus."""

from __future__ import annotations

import asyncio

from harness.bus import (
    STREAM_INBOUND,
    InMemoryQueueBus,
)


async def test_publish_and_consume_one() -> None:
    bus = InMemoryQueueBus()
    await bus.publish(STREAM_INBOUND, {"text": "hi"})
    agen = bus.consume(STREAM_INBOUND, "g1", "c1")
    msg = await asyncio.wait_for(agen.__anext__(), timeout=1.0)
    assert msg.stream == STREAM_INBOUND
    assert msg.data == {"text": "hi"}
    await bus.close()


async def test_each_consumer_group_sees_message_once() -> None:
    bus = InMemoryQueueBus()
    await bus.publish(STREAM_INBOUND, {"n": 1})
    await bus.publish(STREAM_INBOUND, {"n": 2})

    async def drain(group: str) -> list[dict]:
        out: list[dict] = []
        agen = bus.consume(STREAM_INBOUND, group, "c")
        for _ in range(2):
            msg = await asyncio.wait_for(agen.__anext__(), timeout=1.0)
            out.append(msg.data)
        return out

    a = await drain("ga")
    b = await drain("gb")
    assert a == [{"n": 1}, {"n": 2}]
    assert b == [{"n": 1}, {"n": 2}]
    await bus.close()


async def test_consume_blocks_until_publish() -> None:
    bus = InMemoryQueueBus()
    agen = bus.consume(STREAM_INBOUND, "g", "c")

    async def produce() -> None:
        await asyncio.sleep(0.05)
        await bus.publish(STREAM_INBOUND, {"hello": "world"})

    producer = asyncio.create_task(produce())
    msg = await asyncio.wait_for(agen.__anext__(), timeout=1.0)
    await producer
    assert msg.data == {"hello": "world"}
    await bus.close()


async def test_length_reflects_published_count() -> None:
    bus = InMemoryQueueBus()
    assert await bus.length(STREAM_INBOUND) == 0
    await bus.publish(STREAM_INBOUND, {"a": 1})
    await bus.publish(STREAM_INBOUND, {"a": 2})
    assert await bus.length(STREAM_INBOUND) == 2
    await bus.close()
