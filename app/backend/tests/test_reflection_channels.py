"""Tests for the reflection worker + channel adapters."""

from __future__ import annotations

import tempfile

from harness.bus import (
    STREAM_INBOUND,
    STREAM_REPLIES,
    InMemoryQueueBus,
)
from harness.channels import InMemoryAdapter, _NotWiredAdapter
from harness.dispatcher import Dispatcher
from harness.envelope import (
    InboundEnvelope,
    OutboundEnvelope,
    TrustLevel,
)
from harness.reflection import reflect
from harness.registry import HarnessRegistry
from harness.store import FilesystemStore
from harness.tools import build_default_tool_registry
from harness.trace import TraceRecorder
from harness.workflow import WorkflowStatus


async def test_reflect_promotes_after_three_cold_runs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = FilesystemStore(tmp)
        reg = HarnessRegistry(store)
        rec = TraceRecorder(store=store)
        tools, _ = build_default_tool_registry()
        disp = Dispatcher(tools, reg, rec)

        # Three cold scrape sessions — different URLs, same intent shape.
        for i in range(3):
            env = InboundEnvelope(
                source_channel="cli",
                source_address="t",
                trust=TrustLevel.ADMIN,
                payload={"text": f"scrape https://example.com/listing/{i}"},
            )
            r = await disp.handle(env)
            assert r.used_harness is False

        # Reflection should now promote.
        result = await reflect(store, reg, tools, min_hits=3)
        assert len(result.workflows_activated) == 1
        wf_id = result.workflows_activated[0]
        wf = reg.get_workflow(wf_id)
        assert wf is not None
        assert wf.status in (WorkflowStatus.ACTIVE, WorkflowStatus.COMPILED)

        # The fourth scrape should now hit the harness.
        env4 = InboundEnvelope(
            source_channel="cli",
            source_address="t",
            trust=TrustLevel.ADMIN,
            payload={"text": "scrape https://example.com/listing/99"},
        )
        warm = await disp.handle(env4)
        assert warm.used_harness is True
        assert warm.llm_tokens == 0


async def test_reflect_emits_codegen_module() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = FilesystemStore(tmp)
        reg = HarnessRegistry(store)
        rec = TraceRecorder(store=store)
        tools, _ = build_default_tool_registry()
        disp = Dispatcher(tools, reg, rec)
        for i in range(3):
            env = InboundEnvelope(
                source_channel="cli",
                source_address="t",
                trust=TrustLevel.ADMIN,
                payload={"text": f"scrape https://example.com/listing/{i}"},
            )
            await disp.handle(env)

        result = await reflect(store, reg, tools, min_hits=3, codegen_enabled=True)
        assert len(result.generated_tools_created) == 1
        tool_id = result.generated_tools_created[0]
        gen = reg.get_generated_tool(tool_id)
        assert gen is not None
        assert gen.tests_passed is True


async def test_in_memory_adapter_round_trip_through_queue() -> None:
    bus = InMemoryQueueBus()
    adapter = InMemoryAdapter("cli", TrustLevel.ADMIN, bus)

    # User-side: submit
    msg_id = await adapter.submit(
        {"text": "scrape https://x.com/listing/1"}, source_address="terminal"
    )
    assert msg_id

    # Sanity: the envelope landed on agents:inbound with the right shape.
    agen = bus.consume(STREAM_INBOUND, "test-group", "t")
    msg = await agen.__anext__()
    env = InboundEnvelope.from_dict(msg.data)
    assert env.source_channel == "cli"
    assert env.trust == TrustLevel.ADMIN
    assert env.payload["text"].startswith("scrape")

    # Dispatcher-side: publish a reply targeted at the cli channel.
    reply = OutboundEnvelope(
        in_reply_to=env.message_id,
        target_channel="cli",
        target_address="terminal",
        payload={"text": "done"},
        harness_hit=None,
    )
    await bus.publish(STREAM_REPLIES, reply.to_dict())

    # Adapter delivers it locally.
    await adapter.consume_replies_for("cli")
    assert len(adapter.delivered) == 1
    assert adapter.delivered[0].payload["text"] == "done"

    await bus.close()


async def test_not_wired_adapters_raise_at_submit() -> None:
    a = _NotWiredAdapter()
    try:
        await a.submit({}, "x")
    except NotImplementedError:
        return
    raise AssertionError("expected NotImplementedError")
