"""Tests for envelope models."""

from __future__ import annotations

from harness.envelope import (
    InboundEnvelope,
    OutboundEnvelope,
    TrustLevel,
)


def test_inbound_round_trip() -> None:
    env = InboundEnvelope(
        source_channel="cli",
        source_address="terminal",
        trust=TrustLevel.ADMIN,
        payload={"text": "scrape https://example.com/listing/1"},
    )
    restored = InboundEnvelope.from_dict(env.to_dict())
    assert restored.source_channel == env.source_channel
    assert restored.source_address == env.source_address
    assert restored.trust == TrustLevel.ADMIN
    assert restored.payload == env.payload
    assert restored.message_id == env.message_id
    assert restored.correlation_id == env.correlation_id
    assert restored.enqueued_at == env.enqueued_at


def test_outbound_carries_harness_hit() -> None:
    out = OutboundEnvelope(
        in_reply_to="m-1",
        target_channel="cli",
        target_address="terminal",
        payload={"text": "done"},
        harness_hit="workflow:scrape_listing",
    )
    restored = OutboundEnvelope.from_dict(out.to_dict())
    assert restored.harness_hit == "workflow:scrape_listing"


def test_outbound_default_harness_hit_is_none() -> None:
    out = OutboundEnvelope(
        in_reply_to="m-1",
        target_channel="cli",
        target_address="terminal",
        payload={"text": "done"},
    )
    assert out.harness_hit is None
    assert OutboundEnvelope.from_dict(out.to_dict()).harness_hit is None


def test_trust_level_serializes_as_string() -> None:
    env = InboundEnvelope(
        source_channel="telegram",
        source_address="chat-99",
        trust=TrustLevel.USER,
        payload={},
    )
    assert env.to_dict()["trust"] == "user"


def test_message_ids_are_unique() -> None:
    a = InboundEnvelope("cli", "t", TrustLevel.ADMIN, {})
    b = InboundEnvelope("cli", "t", TrustLevel.ADMIN, {})
    assert a.message_id != b.message_id
