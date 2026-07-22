"""Dispatcher agent — the entry point.

On every inbound envelope:

1. Check the harness registry for a promoted hit (generated tool > workflow).
2. If hit, run it and reply (the "warm" path).
3. If miss, run the "reason+act" loop: a mocked LLM picks tools to call
   one at a time. Every tool call is traced.
4. After the session, enqueue a reflection job so the background worker
   can detect patterns and promote.

The LLM is mocked in v0.1: a deterministic policy that knows the scraper
flow (fetch → parse → format). This keeps the demo runnable without a
network call, while preserving the trace shape a real LLM would produce.
When you wire a real Gemini call, only ``_LLMPolicy.choose`` changes.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from .envelope import InboundEnvelope, OutboundEnvelope, TrustLevel
from .registry import HarnessRegistry
from .runner import WorkflowRunner, _render_args
from .codegen import import_generated
from .tools import ToolRegistry
from .trace import TraceRecorder, TraceStep


PRIVILEGED_ACTIONS = {"promote_workflow", "compile_to_code", "shutdown"}


@dataclass
class DispatchResult:
    """Everything the dispatcher learned about handling one envelope."""

    reply: OutboundEnvelope
    session_id: str
    used_harness: bool
    llm_tokens: int
    duration_ms: float


class _LLMPolicy:
    """Mocked LLM that picks tools for the scraper flow.

    The policy advances through a fixed plan based on what's already been
    bound to the session ctx. Each ``choose`` call costs ``cost_per_call``
    pseudo-tokens AND a small simulated think-latency (``think_latency_ms``)
    so the cold-vs-warm wall-clock delta is visible without a real LLM in
    the loop. Real LLM swap-in replaces both.
    """

    cost_per_call = 350
    think_latency_ms = 30.0  # ~30ms per step roughly mimics a fast hosted LLM.

    async def choose(self, intent: str, ctx: dict[str, Any]) -> tuple[str, dict, str]:
        import asyncio
        await asyncio.sleep(self.think_latency_ms / 1000.0)
        """Return (tool_name, args, bind_name) or ('done', {}, '')."""
        intent_l = intent.lower()
        if "fetch_url_0" not in ctx:
            url = ctx.get("params", {}).get("url")
            if url is None:
                # No URL to scrape — a real LLM would not call fetch_url
                # without a target. Return done; the dispatcher emits an
                # empty reply, which is the honest "I can't help with this
                # using my current tools" response.
                return "done", {}, ""
            return "fetch_url", {"url": url}, "fetch_url_0"
        if "parse_listing_1" not in ctx:
            return (
                "parse_listing",
                {"html": ctx["fetch_url_0"]},
                "parse_listing_1",
            )
        if "format_listing_2" not in ctx and "scrape" in intent_l:
            return (
                "format_listing",
                {"listing": ctx["parse_listing_1"]},
                "format_listing_2",
            )
        return "done", {}, ""


class Dispatcher:
    """Reason-then-act loop with harness-first lookup."""

    name = "dispatcher"

    def __init__(
        self,
        tools: ToolRegistry,
        registry: HarnessRegistry,
        recorder: TraceRecorder,
        runner: WorkflowRunner | None = None,
        policy: _LLMPolicy | None = None,
    ) -> None:
        self._tools = tools
        self._reg = registry
        self._rec = recorder
        self._runner = runner or WorkflowRunner(tools)
        self._policy = policy or _LLMPolicy()

    async def handle(self, env: InboundEnvelope) -> DispatchResult:
        # Trust gate (the "loyalty" hook).
        if env.payload.get("action") in PRIVILEGED_ACTIONS and env.trust != TrustLevel.ADMIN:
            return self._reject_unprivileged(env)

        intent = env.payload.get("text") or env.payload.get("intent") or ""
        params = env.payload.get("params") or _extract_params(intent)
        session_id = f"sess-{env.message_id}"
        self._rec.start_session(intent, session_id)
        started = time.perf_counter()

        # ---- Harness-first lookup ----
        hit = self._reg.lookup(intent)
        if hit is not None:
            try:
                if hit.kind == "generated_tool" and hit.generated_tool is not None:
                    mod = import_generated(hit.generated_tool.tool_id)
                    output = await mod.run(self._tools, params)
                    self._rec.record(
                        TraceStep(
                            session_id=session_id,
                            agent=self.name,
                            tool=f"generated:{hit.generated_tool.tool_id}",
                            args=params,
                            result_summary=_summarize(output),
                            duration_ms=(time.perf_counter() - started) * 1000.0,
                            llm_tokens=0,
                        )
                    )
                else:
                    run = await self._runner.run(hit.workflow, params)
                    output = run.output
                    self._rec.record(
                        TraceStep(
                            session_id=session_id,
                            agent=self.name,
                            tool=f"workflow:{hit.workflow.id}",
                            args=params,
                            result_summary=_summarize(output),
                            duration_ms=run.duration_ms,
                            llm_tokens=0,
                        )
                    )
                self._reg.bump_hits(hit.workflow.id)
                self._rec.finalize(session_id, succeeded=True)
                elapsed = (time.perf_counter() - started) * 1000.0
                return DispatchResult(
                    reply=self._reply(env, output, harness_hit=hit.harness_hit_label),
                    session_id=session_id,
                    used_harness=True,
                    llm_tokens=0,
                    duration_ms=elapsed,
                )
            except Exception as exc:
                # Quarantine + fall through to LLM-reasoning path.
                self._reg.quarantine(hit.workflow.id, reason=str(exc))

        # ---- Cold path: reason+act loop ----
        ctx: dict[str, Any] = {
            "params": params,
            # Pre-bake the tool catalogue so the LLM policy doesn't have to
            # re-look-them-up every step. Mock policy ignores this key.
            "_tools_catalogue": "\n".join(
                f"- {n}: {self._tools.get(n).description}"
                for n in self._tools.names()
            ),
        }
        total_llm = 0
        max_steps = 8
        for step_idx in range(max_steps):
            tool_name, args, bind = await self._policy.choose(intent, ctx)
            total_llm += self._policy.cost_per_call
            if tool_name == "done":
                break
            if tool_name not in self._tools:
                self._rec.record(
                    TraceStep(
                        session_id=session_id,
                        agent=self.name,
                        tool=tool_name,
                        args=args,
                        result_summary="unknown tool",
                        duration_ms=0.0,
                        llm_tokens=self._policy.cost_per_call,
                        success=False,
                        error=f"unknown tool: {tool_name}",
                    )
                )
                self._rec.finalize(session_id, succeeded=False)
                elapsed = (time.perf_counter() - started) * 1000.0
                return DispatchResult(
                    reply=self._reply(env, f"unknown tool: {tool_name}"),
                    session_id=session_id,
                    used_harness=False,
                    llm_tokens=total_llm,
                    duration_ms=elapsed,
                )
            # The real LLM references prior results / params with {{bind}} and
            # {{params.x}} tokens; resolve them to concrete values the same way
            # the WorkflowRunner does before invoking the tool.
            resolved = _render_args(args, ctx)
            # Auto-name the bind when the model omits one so the result stays
            # referenceable and the recorded trace is clean + clusterable.
            bind = bind or f"{tool_name}_{step_idx}"
            t0 = time.perf_counter()
            try:
                result = await self._tools.get(tool_name).fn(**resolved)
                dur = (time.perf_counter() - t0) * 1000.0
            except Exception as exc:  # noqa: BLE001
                # Don't crash the whole request on one bad tool call; record
                # the failure (so it won't be clustered/promoted) and stop.
                self._rec.record(
                    TraceStep(
                        session_id=session_id,
                        agent=self.name,
                        tool=tool_name,
                        args=resolved,
                        result_summary=f"error: {exc}",
                        duration_ms=(time.perf_counter() - t0) * 1000.0,
                        llm_tokens=self._policy.cost_per_call,
                        success=False,
                        error=str(exc),
                    )
                )
                break
            ctx[bind] = result
            self._rec.record(
                TraceStep(
                    session_id=session_id,
                    agent=self.name,
                    tool=tool_name,
                    # Record the *resolved* args (concrete values) so the
                    # pattern compiler can recognise prior-step results and
                    # param placeholders when it builds the workflow.
                    args=resolved,
                    result_summary=_summarize(result),
                    duration_ms=dur,
                    llm_tokens=self._policy.cost_per_call,
                )
            )

        last_bind = next(
            reversed([k for k in ctx if k != "params" and not k.startswith("_")]),
            None,
        )
        output = ctx.get(last_bind) if last_bind else None
        self._rec.finalize(session_id, succeeded=True)
        elapsed = (time.perf_counter() - started) * 1000.0
        return DispatchResult(
            reply=self._reply(env, output),
            session_id=session_id,
            used_harness=False,
            llm_tokens=total_llm,
            duration_ms=elapsed,
        )

    def _reply(
        self, env: InboundEnvelope, body: Any, harness_hit: str | None = None
    ) -> OutboundEnvelope:
        return OutboundEnvelope(
            in_reply_to=env.message_id,
            target_channel=env.source_channel,
            target_address=env.source_address,
            payload={"text": str(body) if body is not None else ""},
            harness_hit=harness_hit,
        )

    def _reject_unprivileged(self, env: InboundEnvelope) -> DispatchResult:
        reply = self._reply(
            env,
            "Refused: this action requires an admin channel.",
        )
        # No session was started; nothing to finalize.
        return DispatchResult(
            reply=reply,
            session_id="",
            used_harness=False,
            llm_tokens=0,
            duration_ms=0.0,
        )


def _extract_params(text: str) -> dict[str, Any]:
    """Pull obvious params out of a freeform intent. v0.1: URLs only."""
    import re

    m = re.search(r"https?://\S+", text)
    if m:
        return {"url": m.group(0)}
    return {}


def _summarize(value: Any) -> str:
    s = str(value)
    return s if len(s) <= 200 else s[:200] + "..."
