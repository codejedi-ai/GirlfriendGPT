"""Tests for the dispatcher.

Three things to prove:
1. Cold path runs LLM-reasoning, records traces, bills LLM tokens.
2. Warm path (after a workflow is registered) skips the LLM and
   surfaces a harness_hit label.
3. Admin trust gate rejects USER-trust privileged actions.
"""

from __future__ import annotations

import tempfile

from harness.dispatcher import Dispatcher
from harness.envelope import InboundEnvelope, TrustLevel
from harness.registry import HarnessRegistry
from harness.store import FilesystemStore
from harness.tools import build_default_tool_registry
from harness.trace import TraceRecorder
from harness.workflow import WorkflowSpec, WorkflowStatus, WorkflowStep


def _inbound(text: str, trust: TrustLevel = TrustLevel.ADMIN) -> InboundEnvelope:
    return InboundEnvelope(
        source_channel="cli",
        source_address="terminal",
        trust=trust,
        payload={"text": text},
    )


def _bundle(tmp: str):
    store = FilesystemStore(tmp)
    reg = HarnessRegistry(store)
    rec = TraceRecorder(store=store)
    tools, _ = build_default_tool_registry()
    return Dispatcher(tools, reg, rec), reg, rec, store


async def test_cold_path_runs_reason_and_act() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        disp, reg, rec, _ = _bundle(tmp)
        env = _inbound("scrape https://example.com/listing/1")
        result = await disp.handle(env)
        assert result.used_harness is False
        # 3 tool steps (fetch, parse, format) at 350 tokens/step = 1050+ for
        # reasoning, plus the final "done" decision.
        assert result.llm_tokens >= 1050
        assert result.reply.harness_hit is None
        # Output looks like the formatter's shape.
        assert "Price:" in result.reply.payload["text"]
        # Trace was finalized to the store.
        keys = list(rec._store.list("traces"))  # type: ignore[attr-defined]
        assert len(keys) == 1


async def test_warm_path_hits_workflow_and_skips_llm() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        disp, reg, rec, _ = _bundle(tmp)
        wf = WorkflowSpec(
            id="scrape_listing",
            version=1,
            intent_keywords=["scrape"],
            required_params=["url"],
            steps=[
                WorkflowStep(
                    tool="fetch_url",
                    args={"url": "{{ params.url }}"},
                    bind="fetch_url_0",
                ),
                WorkflowStep(
                    tool="parse_listing",
                    args={"html": "{{ fetch_url_0 }}"},
                    bind="parse_listing_1",
                ),
                WorkflowStep(
                    tool="format_listing",
                    args={"listing": "{{ parse_listing_1 }}"},
                    bind="format_listing_2",
                ),
            ],
            output_template="{{ format_listing_2 }}",
            source_traces=[],
            status=WorkflowStatus.ACTIVE,
        )
        reg.register_workflow(wf)
        result = await disp.handle(_inbound("scrape https://example.com/listing/9"))
        assert result.used_harness is True
        assert result.llm_tokens == 0
        assert result.reply.harness_hit == "workflow:scrape_listing"
        assert "Price:" in result.reply.payload["text"]


async def test_warm_path_is_faster_than_cold() -> None:
    """Smoke check of the verify-criterion-1 direction (cold > warm)."""
    with tempfile.TemporaryDirectory() as tmp:
        disp, reg, _, _ = _bundle(tmp)
        cold = await disp.handle(_inbound("scrape https://example.com/listing/1"))
        # Register a workflow now so the next call goes warm.
        wf = WorkflowSpec(
            id="scrape_listing",
            version=1,
            intent_keywords=["scrape"],
            required_params=["url"],
            steps=[
                WorkflowStep(tool="fetch_url", args={"url": "{{ params.url }}"}, bind="fetch_url_0"),
                WorkflowStep(tool="parse_listing", args={"html": "{{ fetch_url_0 }}"}, bind="parse_listing_1"),
                WorkflowStep(tool="format_listing", args={"listing": "{{ parse_listing_1 }}"}, bind="format_listing_2"),
            ],
            output_template="{{ format_listing_2 }}",
            source_traces=[],
            status=WorkflowStatus.ACTIVE,
        )
        reg.register_workflow(wf)
        warm = await disp.handle(_inbound("scrape https://example.com/listing/2"))
        assert warm.used_harness is True
        # LLM tokens drop to zero on the warm path — the canonical "fewer
        # LLM calls" demonstration from VERIFY criterion 1.
        assert warm.llm_tokens == 0 and cold.llm_tokens > 0


async def test_trust_gate_rejects_user_privileged_action() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        disp, _, _, _ = _bundle(tmp)
        env = InboundEnvelope(
            source_channel="telegram",
            source_address="chat-99",
            trust=TrustLevel.USER,
            payload={"action": "promote_workflow"},
        )
        result = await disp.handle(env)
        assert "admin" in result.reply.payload["text"].lower()


async def test_trust_gate_allows_admin_privileged_action() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        disp, _, _, _ = _bundle(tmp)
        env = InboundEnvelope(
            source_channel="cli",
            source_address="terminal",
            trust=TrustLevel.ADMIN,
            payload={"action": "promote_workflow", "text": "scrape https://x.com/listing/1"},
        )
        # ADMIN gets through the trust gate. v0.1: the action isn't handled
        # specially (the cold path runs), but the refusal text is absent.
        result = await disp.handle(env)
        assert "admin" not in result.reply.payload["text"].lower()
