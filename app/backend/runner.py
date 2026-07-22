"""WorkflowRunner — execute a WorkflowSpec against a ToolRegistry.

Step args are Jinja-rendered against a context populated by:
- ``params``: per-invocation parameter dict
- prior steps' bound results

We use a tiny mustache-like renderer rather than full Jinja2 to keep the
core dependency-free. Real workflows can still hit Jinja2 from elsewhere.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from .tools import ToolRegistry
from .workflow import WorkflowSpec


_TEMPLATE_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}")


def render(template: str, ctx: dict[str, Any]) -> Any:
    """Render ``template`` against ``ctx``.

    If the template is exactly one ``{{ var }}`` reference, return the
    referenced value as-is (preserving types). Otherwise do string substitution.
    """
    m = _TEMPLATE_RE.fullmatch(template.strip())
    if m is not None:
        return _resolve(m.group(1), ctx)

    def _sub(match: "re.Match[str]") -> str:
        return str(_resolve(match.group(1), ctx))

    return _TEMPLATE_RE.sub(_sub, template)


def _resolve(path: str, ctx: dict[str, Any]) -> Any:
    parts = path.split(".")
    cur: Any = ctx
    for p in parts:
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            cur = getattr(cur, p, None)
        if cur is None:
            return None
    return cur


def _render_args(args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in args.items():
        if isinstance(v, str):
            out[k] = render(v, ctx)
        elif isinstance(v, dict):
            out[k] = _render_args(v, ctx)
        elif isinstance(v, list):
            out[k] = [render(x, ctx) if isinstance(x, str) else x for x in v]
        else:
            out[k] = v
    return out


@dataclass
class RunResult:
    output: Any
    duration_ms: float
    steps_executed: int
    binds: dict[str, Any]


class WorkflowRunner:
    """Executes WorkflowSpec sequentially against a ToolRegistry."""

    def __init__(self, tools: ToolRegistry) -> None:
        self._tools = tools

    async def run(self, spec: WorkflowSpec, params: dict[str, Any]) -> RunResult:
        # Validate required params up front so we fail loud and replay-safe.
        missing = [p for p in spec.required_params if p not in params]
        if missing:
            raise ValueError(f"workflow {spec.id} missing params: {missing}")

        ctx: dict[str, Any] = {"params": params}
        started = time.perf_counter()
        executed = 0
        for step in spec.steps:
            if step.tool not in self._tools:
                raise KeyError(
                    f"workflow {spec.id} step references unknown tool {step.tool!r}"
                )
            tool = self._tools.get(step.tool)
            args = _render_args(step.args, ctx)
            result = await tool.fn(**args)
            if step.bind:
                ctx[step.bind] = result
            executed += 1

        output = (
            render(spec.output_template, ctx) if spec.output_template else None
        )
        elapsed = (time.perf_counter() - started) * 1000.0
        binds = {k: v for k, v in ctx.items() if k != "params"}
        return RunResult(
            output=output,
            duration_ms=elapsed,
            steps_executed=executed,
            binds=binds,
        )
