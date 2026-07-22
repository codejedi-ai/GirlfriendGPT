"""Tests for WorkflowRunner + deterministic codegen."""

from __future__ import annotations

import tempfile
from pathlib import Path

from harness.codegen import (
    codegen_from_workflow,
    codegen_source,
    import_generated,
    regression_test_generated,
)
from harness.registry import HarnessRegistry
from harness.runner import WorkflowRunner, render
from harness.store import FilesystemStore
from harness.tools import build_default_tool_registry
from harness.workflow import WorkflowSpec, WorkflowStatus, WorkflowStep


def test_render_single_var_preserves_type() -> None:
    ctx = {"x": {"a": 42}}
    assert render("{{ x.a }}", ctx) == 42
    assert render("value={{ x.a }}", ctx) == "value=42"


def test_render_returns_none_for_missing() -> None:
    assert render("{{ nope.here }}", {}) is None


def _scrape_workflow() -> WorkflowSpec:
    return WorkflowSpec(
        id="scrape_listing",
        version=1,
        intent_keywords=["scrape", "listing"],
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


async def test_workflow_runner_executes_sequence() -> None:
    tools, _ = build_default_tool_registry()
    spec = _scrape_workflow()
    runner = WorkflowRunner(tools)
    result = await runner.run(spec, {"url": "https://example.com/listing/42"})
    assert result.steps_executed == 3
    assert isinstance(result.output, str)
    assert "Price:" in result.output
    assert "Bedrooms:" in result.output
    assert "Address:" in result.output


async def test_workflow_runner_validates_required_params() -> None:
    tools, _ = build_default_tool_registry()
    runner = WorkflowRunner(tools)
    try:
        await runner.run(_scrape_workflow(), {})
    except ValueError as e:
        assert "missing params" in str(e)
        return
    raise AssertionError("expected ValueError for missing url")


async def test_workflow_runner_raises_on_unknown_tool() -> None:
    tools, _ = build_default_tool_registry()
    bad = WorkflowSpec(
        id="bad",
        version=1,
        intent_keywords=[],
        required_params=[],
        steps=[WorkflowStep(tool="not_a_tool", args={})],
        output_template="",
    )
    runner = WorkflowRunner(tools)
    try:
        await runner.run(bad, {})
    except KeyError as e:
        assert "not_a_tool" in str(e)
        return
    raise AssertionError("expected KeyError for unknown tool")


def test_codegen_source_is_importable_python() -> None:
    spec = _scrape_workflow()
    src = codegen_source(spec)
    # Lightweight syntactic check — actual run-import is exercised below.
    compile(src, "<generated>", "exec")
    assert "async def run" in src
    assert "fetch_url" in src
    assert "parse_listing" in src


async def test_codegen_round_trip_writes_disk_and_runs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = FilesystemStore(tmp)
        reg = HarnessRegistry(store)
        spec = _scrape_workflow()
        reg.register_workflow(spec)

        gen = codegen_from_workflow(spec, store, reg)
        assert Path(gen.disk_path).exists()
        assert store.exists(gen.store_key)

        tools, _ = build_default_tool_registry()
        mod = import_generated(gen.tool_id)
        out = await mod.run(tools, {"url": "https://example.com/listing/7"})
        assert isinstance(out, str)
        assert "Price:" in out


async def test_regression_test_promotes_only_on_green() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = FilesystemStore(tmp)
        reg = HarnessRegistry(store)
        spec = _scrape_workflow()
        reg.register_workflow(spec)
        gen = codegen_from_workflow(spec, store, reg)
        tools, _ = build_default_tool_registry()

        good = await regression_test_generated(
            gen,
            spec,
            tools,
            {"url": "https://example.com/listing/3"},
            lambda out: isinstance(out, str) and "Price:" in out,
        )
        assert good is True

        bad = await regression_test_generated(
            gen,
            spec,
            tools,
            {"url": "https://example.com/listing/3"},
            lambda out: out == "this never happens",
        )
        assert bad is False
