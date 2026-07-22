"""Pattern detector — cluster traces, then compile into workflows.

For v0.1 we use a simple exact-match clustering: traces with the same
(intent_hash, tool_seq_hash) are one cluster. That's enough to demonstrate
the loop. Real implementation will use Jaccard similarity on tool names
and clustering on intent embeddings (TODO when LLM is wired).

A cluster crosses the **promotion threshold** when it accumulates
``min_hits`` successful traces. The compiler then emits a ``WorkflowSpec``.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .trace import TraceStep, intent_hash, load_trace_jsonl, tool_seq_hash
from .workflow import WorkflowSpec, WorkflowStatus, WorkflowStep


@dataclass
class Cluster:
    """A group of similar successful traces."""

    intent_hash: str
    tool_seq_hash: str
    trace_paths: list[str]
    sample_intent: str
    sample_tools: list[str]
    sample_steps: list[TraceStep]  # From the first trace; used for codegen


@dataclass
class LoadedTrace:
    path: str
    header: dict
    steps: list[TraceStep]


def cluster_traces(
    loaded: Iterable[LoadedTrace], min_hits: int = 3
) -> list[Cluster]:
    """Group traces by (intent_hash, tool_seq_hash); keep clusters >= min_hits.

    Only successful traces are clustered — we don't want to learn failures.
    """
    by_key: dict[tuple[str, str], list[LoadedTrace]] = defaultdict(list)
    for lt in loaded:
        if not lt.header.get("succeeded", False):
            continue
        key = (lt.header["intent_hash"], lt.header["tool_seq_hash"])
        by_key[key].append(lt)

    clusters: list[Cluster] = []
    for (ih, tsh), members in by_key.items():
        if len(members) < min_hits:
            continue
        first = members[0]
        clusters.append(
            Cluster(
                intent_hash=ih,
                tool_seq_hash=tsh,
                trace_paths=[m.path for m in members],
                sample_intent=first.header["intent_text"],
                sample_tools=[s.tool for s in first.steps if s.success],
                sample_steps=first.steps,
            )
        )
    return clusters


def load_all_traces(store, prefix: str = "traces") -> list[LoadedTrace]:
    """Read every JSONL trace under ``prefix`` from ``store``."""
    out: list[LoadedTrace] = []
    for key in store.list(prefix):
        if not key.endswith(".jsonl"):
            continue
        header, steps = load_trace_jsonl(store.get(key))
        out.append(LoadedTrace(path=key, header=header, steps=steps))
    return out


# ---------- compiler ----------


def compile_workflow(cluster: Cluster, workflow_id: str) -> WorkflowSpec:
    """Emit a WorkflowSpec from a cluster's sample trace.

    v0.1 strategy: take the sample trace's tool sequence verbatim, replace
    leaf string values that look like params (URLs, IDs) with Jinja
    placeholders, and bind each step's result by tool name.
    """
    keywords = [w for w in cluster.sample_intent.lower().split() if not _is_param(w)]
    required: list[str] = []
    steps: list[WorkflowStep] = []

    for i, s in enumerate(cluster.sample_steps):
        if not s.success:
            continue
        rendered_args: dict[str, str | int | float | bool | list | dict] = {}
        for arg_name, arg_val in s.args.items():
            # Order matters: a long HTML blob has digits in it, so we must
            # check "earlier-step result" before "looks like a user param".
            if _is_prior_result(arg_val, steps):
                rendered_args[arg_name] = _placeholder_for_earlier(arg_val, steps)
            elif isinstance(arg_val, str) and _is_param(arg_val):
                placeholder = f"{{{{ params.{arg_name} }}}}"
                rendered_args[arg_name] = placeholder
                if arg_name not in required:
                    required.append(arg_name)
            else:
                rendered_args[arg_name] = arg_val
        steps.append(
            WorkflowStep(
                tool=s.tool,
                args=rendered_args,
                bind=_bind_name(s.tool, i),
            )
        )

    # Default: last step's result is the workflow output.
    if steps:
        output_template = f"{{{{ {steps[-1].bind} }}}}"
    else:
        output_template = ""

    return WorkflowSpec(
        id=workflow_id,
        version=1,
        intent_keywords=keywords[:5] or [cluster.sample_intent[:20]],
        required_params=required,
        steps=steps,
        output_template=output_template,
        source_traces=cluster.trace_paths,
        status=WorkflowStatus.DRAFT,
    )


def _is_param(s: str) -> bool:
    """Heuristic: URLs and digit-bearing tokens are parameters."""
    if s.startswith("http://") or s.startswith("https://"):
        return True
    if any(ch.isdigit() for ch in s):
        return True
    return False


def _bind_name(tool: str, idx: int) -> str:
    # Last segment of dotted tool name, plus index for uniqueness.
    leaf = tool.rsplit(".", 1)[-1]
    return f"{leaf}_{idx}"


def _is_prior_result(value: object, prev_steps: list[WorkflowStep]) -> bool:
    """Heuristic for v0.1: in a sequential pipeline, complex args are almost
    always prior-step results. Specifically: any dict/list, or any non-URL
    string longer than 40 chars, when a prior step exists.

    Real implementation will match by object identity / hash against the
    recorded result fingerprints once we add result-fingerprinting to
    TraceStep.
    """
    if not prev_steps:
        return False
    if isinstance(value, (dict, list)):
        return True
    if isinstance(value, str):
        if value.startswith("http://") or value.startswith("https://"):
            return False
        if len(value) > 40:
            return True
    return False


def _placeholder_for_earlier(value: object, prev_steps: list[WorkflowStep]) -> str:
    # Just bind to most recent prior step. Good enough for v0.1 linear flows.
    if not prev_steps:
        return value if isinstance(value, str) else str(value)
    return f"{{{{ {prev_steps[-1].bind} }}}}"
