"""Tests for trace recorder + fingerprinting + filesystem store."""

from __future__ import annotations

import tempfile
from pathlib import Path

from harness.store import FilesystemStore
from harness.trace import (
    TraceRecorder,
    TraceStep,
    intent_hash,
    load_trace_jsonl,
    normalize_intent,
    tool_seq_hash,
)


def test_normalize_intent_strips_urls_and_digits() -> None:
    a = normalize_intent("scrape https://example.com/listing/1")
    b = normalize_intent("scrape https://example.com/listing/99")
    assert a == b
    # URLs collapse to nothing (the literal "URL" replacement is stripped by
    # the non-alpha regex). For v0.1 that's enough: both intents cluster.
    assert a == "scrape"
    # Bare digits in non-URL text become "n".
    assert normalize_intent("fetch item 42") == "fetch item n"


def test_intent_hash_matches_for_similar_requests() -> None:
    a = intent_hash("scrape https://example.com/listing/1")
    b = intent_hash("scrape https://example.com/listing/42")
    c = intent_hash("analyze https://example.com/listing/1")
    assert a == b
    assert a != c


def test_tool_seq_hash_distinguishes_order() -> None:
    assert tool_seq_hash(["a", "b", "c"]) != tool_seq_hash(["a", "c", "b"])
    assert tool_seq_hash(["a", "b"]) == tool_seq_hash(["a", "b"])


def test_recorder_session_lifecycle() -> None:
    r = TraceRecorder()
    sess = r.start_session("scrape https://example.com/listing/1", "s-1")
    r.record(
        TraceStep(
            session_id="s-1",
            agent="scraper",
            tool="fetch_url",
            args={"url": "https://example.com/listing/1"},
            result_summary="200 OK",
            duration_ms=12.0,
            llm_tokens=0,
        )
    )
    r.record(
        TraceStep(
            session_id="s-1",
            agent="scraper",
            tool="parse_listing",
            args={"html": "<...>"},
            result_summary="extracted 3 fields",
            duration_ms=5.0,
            llm_tokens=120,
        )
    )
    r.finalize("s-1", succeeded=True)
    assert sess.tool_sequence == ["fetch_url", "parse_listing"]
    assert sess.total_llm_tokens == 120
    assert sess.succeeded is True


def test_recorder_persists_to_store_and_round_trips() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = FilesystemStore(Path(tmp))
        r = TraceRecorder(store=store)
        r.start_session("scrape https://example.com/listing/1", "s-2")
        r.record(
            TraceStep(
                session_id="s-2",
                agent="scraper",
                tool="fetch_url",
                args={"url": "https://example.com/listing/1"},
                result_summary="200 OK",
                duration_ms=12.0,
            )
        )
        key = r.finalize("s-2", succeeded=True)
        assert key is not None
        assert store.exists(key)
        header, steps = load_trace_jsonl(store.get(key))
        assert header["session_id"] == "s-2"
        assert header["intent_hash"] == intent_hash(
            "scrape https://example.com/listing/1"
        )
        assert header["tool_seq_hash"] == tool_seq_hash(["fetch_url"])
        assert len(steps) == 1
        assert steps[0].tool == "fetch_url"


def test_recorder_without_store_is_noop_finalize() -> None:
    r = TraceRecorder(store=None)
    r.start_session("x", "s-3")
    assert r.finalize("s-3") is None


def test_filesystem_store_list_prefix() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = FilesystemStore(tmp)
        store.put("traces/2026-06-05/a.jsonl", "a")
        store.put("traces/2026-06-05/b.jsonl", "b")
        store.put("workflows/x.yaml", "x")
        traces = sorted(store.list("traces"))
        assert traces == [
            "traces/2026-06-05/a.jsonl",
            "traces/2026-06-05/b.jsonl",
        ]
        assert sorted(store.list("workflows")) == ["workflows/x.yaml"]


def test_recorder_raises_on_missing_session() -> None:
    r = TraceRecorder()
    try:
        r.record(
            TraceStep(
                session_id="missing",
                agent="a",
                tool="t",
                args={},
                result_summary="",
                duration_ms=0.0,
            )
        )
    except KeyError:
        return
    raise AssertionError("expected KeyError for unknown session")
