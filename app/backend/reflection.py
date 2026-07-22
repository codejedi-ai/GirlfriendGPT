"""Reflection worker — promotes traces into workflows and code.

Runs as a background task: load every trace from the store, cluster by
fingerprint, compile workflows for clusters that cross the threshold, and
(when ``codegen_enabled``) emit Python tools for new workflows that pass
their regression check.

Called explicitly by the demo after each cold run. In production it runs
as its own queue consumer on ``agents:reflection``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .codegen import codegen_from_workflow, regression_test_generated
from .patterns import cluster_traces, compile_workflow, load_all_traces
from .registry import HarnessRegistry
from .store import Store
from .tools import ToolRegistry
from .workflow import WorkflowSpec, WorkflowStatus


@dataclass
class ReflectionResult:
    workflows_created: list[str]
    workflows_activated: list[str]
    generated_tools_created: list[str]


def _suggest_workflow_id(sample_intent: str) -> str:
    # Slug-y id from the first 3 keyword-ish words.
    import re

    words = [
        w
        for w in re.findall(r"[a-zA-Z]+", sample_intent.lower())
        if len(w) >= 3 and w not in {"the", "and", "for", "with", "this", "that"}
    ]
    return "_".join(words[:3]) or "workflow"


async def reflect(
    store: Store,
    registry: HarnessRegistry,
    tools: ToolRegistry,
    *,
    min_hits: int = 3,
    codegen_enabled: bool = True,
    codegen_threshold_hits: int = 0,
    sample_params_for: dict[str, dict[str, Any]] | None = None,
) -> ReflectionResult:
    """One reflection pass.

    ``sample_params_for`` is a per-workflow-id mapping of sample params
    used for the regression test. In production these come from the
    source traces; the demo wires them directly for clarity.
    """
    sample_params_for = sample_params_for or {}
    workflows_created: list[str] = []
    workflows_activated: list[str] = []
    generated: list[str] = []

    loaded = load_all_traces(store)
    clusters = cluster_traces(loaded, min_hits=min_hits)

    for cluster in clusters:
        # Skip if we've already promoted this exact fingerprint to ACTIVE/COMPILED.
        existing = _find_workflow_by_intent_hash(registry, cluster.intent_hash)
        if existing is None:
            wf_id = _unique_id(registry, _suggest_workflow_id(cluster.sample_intent))
            wf = compile_workflow(cluster, wf_id)
            wf.status = WorkflowStatus.ACTIVE  # Promote straight to ACTIVE in v0.1.
            registry.register_workflow(wf)
            workflows_created.append(wf_id)
            workflows_activated.append(wf_id)
            existing = wf

        if codegen_enabled and existing.hits >= codegen_threshold_hits:
            # Only codegen once per workflow id.
            if not any(
                g.workflow_id == existing.id for g in registry._generated.values()  # type: ignore[attr-defined]
            ):
                gen = codegen_from_workflow(existing, store, registry)
                sample_params = sample_params_for.get(
                    existing.id, _infer_sample_params(cluster)
                )
                # Cheap check: produce *any* non-None output.
                ok = await regression_test_generated(
                    gen,
                    existing,
                    tools,
                    sample_params,
                    lambda out: out is not None and out != "",
                )
                if ok:
                    gen.tests_passed = True
                    registry.register_generated_tool(gen)
                    generated.append(gen.tool_id)
                else:
                    registry.quarantine(existing.id, reason="codegen regression failed")
    return ReflectionResult(
        workflows_created=workflows_created,
        workflows_activated=workflows_activated,
        generated_tools_created=generated,
    )


def _find_workflow_by_intent_hash(
    registry: HarnessRegistry, intent_hash: str
) -> WorkflowSpec | None:
    for wf_id, ih in registry._workflow_intent_hashes.items():  # type: ignore[attr-defined]
        if ih == intent_hash:
            return registry.get_workflow(wf_id)
    return None


def _unique_id(registry: HarnessRegistry, base: str) -> str:
    if registry.get_workflow(base) is None:
        return base
    i = 2
    while registry.get_workflow(f"{base}_{i}") is not None:
        i += 1
    return f"{base}_{i}"


def _infer_sample_params(cluster) -> dict[str, Any]:
    # Pull params from the first step's args. v0.1 heuristic.
    if not cluster.sample_steps:
        return {}
    first = cluster.sample_steps[0]
    out: dict[str, Any] = {}
    for k, v in first.args.items():
        if isinstance(v, str) and (
            v.startswith("http://") or v.startswith("https://") or any(c.isdigit() for c in v)
        ):
            out[k] = v
    return out
