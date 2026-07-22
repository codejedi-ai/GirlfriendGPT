"""Tests for WorkflowSpec, pattern detector, compiler, and registry."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from harness.patterns import (
    LoadedTrace,
    cluster_traces,
    compile_workflow,
    load_all_traces,
)
from harness.registry import HarnessRegistry
from harness.store import FilesystemStore
from harness.trace import (
    TraceRecorder,
    TraceStep,
    intent_hash,
    normalize_intent,
    tool_seq_hash,
)
from harness.workflow import WorkflowSpec, WorkflowStatus, WorkflowStep


def _trace(url: str, sid: str) -> tuple[dict, list[TraceStep]]:
    header = {
        "session_id": sid,
        "intent_text": f"scrape {url}",
        "intent_hash": intent_hash(f"scrape {url}"),
        "tool_seq_hash": tool_seq_hash(["fetch_url", "parse_listing"]),
        "succeeded": True,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    steps = [
        TraceStep(
            session_id=sid,
            agent="scraper",
            tool="fetch_url",
            args={"url": url},
            result_summary="200 OK; 14 KB html",
            duration_ms=20.0,
        ),
        TraceStep(
            session_id=sid,
            agent="scraper",
            tool="parse_listing",
            args={"html": "x" * 500},  # Long string -> earlier-result heuristic
            result_summary="extracted listing",
            duration_ms=5.0,
        ),
    ]
    return header, steps


def test_workflow_yaml_round_trip() -> None:
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
        ],
        output_template="{{ parse_listing_1 }}",
        source_traces=["traces/2026-06-05/a.jsonl"],
        status=WorkflowStatus.DRAFT,
    )
    blob = wf.to_yaml()
    restored = WorkflowSpec.from_yaml(blob)
    assert restored.id == wf.id
    assert restored.version == wf.version
    assert restored.intent_keywords == wf.intent_keywords
    assert restored.required_params == wf.required_params
    assert len(restored.steps) == 2
    assert restored.steps[0].tool == "fetch_url"
    assert restored.steps[0].args == {"url": "{{ params.url }}"}
    assert restored.steps[1].bind == "parse_listing_1"
    assert restored.status == WorkflowStatus.DRAFT


def test_cluster_traces_groups_by_fingerprint() -> None:
    loaded = []
    for i in range(3):
        h, steps = _trace(f"https://example.com/listing/{i}", f"s-{i}")
        loaded.append(LoadedTrace(path=f"traces/x/s-{i}.jsonl", header=h, steps=steps))
    # Different intent, same shape
    h2, s2 = _trace("https://example.com/article/1", "diff")
    h2["intent_text"] = "fetch product 1"
    h2["intent_hash"] = intent_hash("fetch product 1")
    loaded.append(LoadedTrace(path="traces/x/diff.jsonl", header=h2, steps=s2))

    clusters = cluster_traces(loaded, min_hits=3)
    assert len(clusters) == 1
    assert len(clusters[0].trace_paths) == 3


def test_cluster_traces_ignores_failures() -> None:
    loaded = []
    for i in range(3):
        h, steps = _trace(f"https://example.com/listing/{i}", f"s-{i}")
        h["succeeded"] = False
        loaded.append(LoadedTrace(path=f"traces/x/s-{i}.jsonl", header=h, steps=steps))
    clusters = cluster_traces(loaded, min_hits=3)
    assert clusters == []


def test_cluster_traces_below_threshold_emits_nothing() -> None:
    loaded = []
    for i in range(2):
        h, steps = _trace(f"https://example.com/listing/{i}", f"s-{i}")
        loaded.append(LoadedTrace(path=f"x/{i}.jsonl", header=h, steps=steps))
    assert cluster_traces(loaded, min_hits=3) == []


def test_compile_workflow_from_cluster() -> None:
    loaded = []
    for i in range(3):
        h, steps = _trace(f"https://example.com/listing/{i}", f"s-{i}")
        loaded.append(LoadedTrace(path=f"x/{i}.jsonl", header=h, steps=steps))
    clusters = cluster_traces(loaded, min_hits=3)
    assert len(clusters) == 1
    wf = compile_workflow(clusters[0], "scrape_listing")
    assert wf.id == "scrape_listing"
    assert "scrape" in wf.intent_keywords
    assert "url" in wf.required_params
    # First step's URL was templated; second step's long-html arg points
    # to the earlier bind.
    assert wf.steps[0].args["url"] == "{{ params.url }}"
    assert wf.steps[1].args["html"] == "{{ fetch_url_0 }}"
    assert wf.output_template == "{{ parse_listing_1 }}"


def test_registry_round_trip_and_lookup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = FilesystemStore(tmp)
        wf = WorkflowSpec(
            id="scrape_listing",
            version=1,
            intent_keywords=["scrape"],
            required_params=["url"],
            steps=[WorkflowStep(tool="fetch_url", args={"url": "{{ params.url }}"}, bind="fetch_url_0")],
            output_template="{{ fetch_url_0 }}",
            source_traces=[],
            status=WorkflowStatus.ACTIVE,
        )
        reg = HarnessRegistry(store)
        reg.register_workflow(wf)

        # Fresh registry on same store should see it.
        reg2 = HarnessRegistry(store)
        reg2.load()
        hit = reg2.lookup("scrape https://example.com/listing/42")
        assert hit is not None
        assert hit.kind == "workflow"
        assert hit.id == "scrape_listing"
        assert hit.harness_hit_label == "workflow:scrape_listing"


def test_registry_skips_draft_and_quarantined() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = FilesystemStore(tmp)
        wf = WorkflowSpec(
            id="scrape_listing",
            version=1,
            intent_keywords=["scrape"],
            required_params=["url"],
            steps=[WorkflowStep(tool="fetch_url", args={"url": "{{ params.url }}"})],
            output_template="",
            source_traces=[],
            status=WorkflowStatus.DRAFT,
        )
        reg = HarnessRegistry(store)
        reg.register_workflow(wf)
        assert reg.lookup("scrape https://x.com/listing/1") is None
        reg.activate("scrape_listing")
        assert reg.lookup("scrape https://x.com/listing/1") is not None
        reg.quarantine("scrape_listing", reason="bad")
        assert reg.lookup("scrape https://x.com/listing/1") is None


def test_load_all_traces_from_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = FilesystemStore(tmp)
        recorder = TraceRecorder(store=store)
        for i in range(2):
            recorder.start_session(f"scrape https://x.com/listing/{i}", f"s-{i}")
            recorder.record(
                TraceStep(
                    session_id=f"s-{i}",
                    agent="scraper",
                    tool="fetch_url",
                    args={"url": f"https://x.com/listing/{i}"},
                    result_summary="ok",
                    duration_ms=1.0,
                )
            )
            recorder.finalize(f"s-{i}", succeeded=True)
        loaded = load_all_traces(store)
        assert len(loaded) == 2
        assert all(lt.header["succeeded"] for lt in loaded)
