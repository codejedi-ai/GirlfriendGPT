"""Queue-driven multi-agent runtime.

The flow, end to end:

    user message
      -> agents:inbound        (channel adapter publishes)
      -> DispatcherAgent       (consumes; decides capability; NO work itself)
      -> agents:tasks          (dispatches a task to a task-specific agent)
      -> TaskAgent             (e.g. the scraper; runs the reason-act/warm loop)
      -> agents:results        (publishes its outcome)
      -> DispatcherAgent       (consumes; finalizes + reflects)
      -> agents:replies        (publishes the reply)
      -> channel               (ChannelClient delivers to the user)

Three pieces:

``DispatcherAgent`` — the coordinator. Routes inbound messages to a task agent
and turns task results into channel replies (and runs reflection). It never
executes tools.

``TaskAgent`` — a worker for one capability. Consumes its tasks, does the
actual work via ``Dispatcher``, and reports results back. The scraper is the
v1 instance.

``ChannelClient`` — the producer/consumer half every adapter shares: publish to
``agents:inbound``, await the correlated reply off ``agents:replies``. The CLI
and the FastAPI/WebSocket frontend drive this same class, so a message typed in
a terminal and one typed in the browser take the identical path — that's why
the CLI has the same effect as the frontend.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import Any

from .bus import (
    STREAM_INBOUND,
    STREAM_REPLIES,
    STREAM_RESULTS,
    STREAM_TASKS,
    QueueBus,
)
from .dispatcher import Dispatcher
from .envelope import InboundEnvelope, OutboundEnvelope, TrustLevel
from .reflection import reflect
from .trace import TraceRecorder


def _summarize(value: Any, limit: int = 120) -> str:
    s = str(value)
    return s if len(s) <= limit else s[:limit] + "..."


def route_capability(env: InboundEnvelope) -> str:
    """Pick which task-specific agent should handle this intent.

    v1 has one task agent ("scraper"); this is the seam where more agents
    (summarizer, classifier, …) get routed as capabilities are added.
    """
    return "scraper"


# --------------------------------------------------------------------------
# Dispatcher agent — router + finalizer (does NO task work itself)
# --------------------------------------------------------------------------


class DispatcherAgent:
    """The coordinator. Two loops, no tool execution of its own:

    inbound:  agents:inbound  -> decide capability -> agents:tasks (dispatch)
    results:  agents:results  -> agents:replies (reply) + reflection

    The actual work happens in a task-specific agent (see TaskAgent), so the
    flow is: user -> queue -> dispatcher -> task agent -> queue -> dispatcher
    -> reply.
    """

    def __init__(
        self,
        bus: QueueBus,
        *,
        store: Any,
        registry: Any,
        tools: Any,
        group: str = "dispatcher",
        consumer: str = "dispatcher-1",
        reflect_min_hits: int = 3,
        reflect_after_each: bool = True,
        inbound_stream: str = STREAM_INBOUND,
        tasks_stream: str = STREAM_TASKS,
        results_stream: str = STREAM_RESULTS,
        replies_stream: str = STREAM_REPLIES,
    ) -> None:
        self._bus = bus
        self._store = store
        self._registry = registry
        self._tools = tools
        self._group = group
        self._consumer = consumer
        self._reflect_min_hits = reflect_min_hits
        self._reflect_after_each = reflect_after_each
        self._inbound = inbound_stream
        self._tasks_stream = tasks_stream
        self._results = results_stream
        self._replies = replies_stream
        self._tasks: list[asyncio.Task] = []
        # Telemetry the e2e/UI can read.
        self.dispatched = 0
        self.replied = 0
        self.last_reflection: Any = None

    def start(self) -> None:
        if not self._tasks:
            self._tasks = [
                asyncio.create_task(self._run_inbound(), name="dispatcher-inbound"),
                asyncio.create_task(self._run_results(), name="dispatcher-results"),
            ]

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await t
        self._tasks = []

    # ---- inbound: route the user message to a task-specific agent ----
    async def _run_inbound(self) -> None:
        async for msg in self._bus.consume(self._inbound, self._group, self._consumer):
            try:
                env = InboundEnvelope.from_dict(msg.data)
                capability = route_capability(env)
                task = {
                    "task_id": f"task-{env.message_id}",
                    "capability": capability,
                    "envelope": env.to_dict(),  # carry the original for correlation
                }
                await self._bus.publish(self._tasks_stream, task)
                self.dispatched += 1
            except Exception:  # noqa: BLE001
                pass
            finally:
                await self._bus.ack(self._inbound, self._group, msg.message_id)

    # ---- results: finalize the task agent's output into a channel reply ----
    async def _run_results(self) -> None:
        async for msg in self._bus.consume(self._results, self._group, self._consumer):
            try:
                reply = OutboundEnvelope.from_dict(msg.data["reply"])
                await self._bus.publish(self._replies, reply.to_dict())
                self.replied += 1
                if self._reflect_after_each:
                    self.last_reflection = await reflect(
                        self._store, self._registry, self._tools,
                        min_hits=self._reflect_min_hits, codegen_enabled=True,
                    )
            except Exception:  # noqa: BLE001
                pass
            finally:
                await self._bus.ack(self._results, self._group, msg.message_id)


# --------------------------------------------------------------------------
# Task-specific agent — does the actual work for one capability
# --------------------------------------------------------------------------


class TaskAgent:
    """A worker for one capability. Consumes ``agents:tasks`` (filtered to its
    capability), runs the reason-act / warm-replay loop via ``Dispatcher``, and
    publishes the outcome to ``agents:results`` for the dispatcher to finalize.

    This is the "task specific Agent" the dispatcher delegates to. The scraper
    is the v1 instance: ``TaskAgent(capability="scraper", dispatcher=...)``.
    """

    def __init__(
        self,
        bus: QueueBus,
        dispatcher: Dispatcher,
        recorder: TraceRecorder,
        *,
        capability: str = "scraper",
        group: str | None = None,
        consumer: str = "agent-1",
        tasks_stream: str = STREAM_TASKS,
        results_stream: str = STREAM_RESULTS,
    ) -> None:
        self._bus = bus
        self._dispatcher = dispatcher
        self._recorder = recorder
        self.capability = capability
        self._group = group or f"agent-{capability}"
        self._consumer = consumer
        self._tasks_stream = tasks_stream
        self._results = results_stream
        self._task: asyncio.Task | None = None
        self.handled = 0

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name=f"agent-{self.capability}")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run(self) -> None:
        async for msg in self._bus.consume(self._tasks_stream, self._group, self._consumer):
            try:
                task = msg.data
                if task.get("capability") != self.capability:
                    # Not for us — ack so this consumer-group moves on. (With
                    # one task agent this never fires; the seam matters when
                    # multiple capabilities share the stream.)
                    continue
                env = InboundEnvelope.from_dict(task["envelope"])
                result = await self._dispatcher.handle(env)
                self.handled += 1
                await self._bus.publish(self._results, {
                    "task_id": task.get("task_id"),
                    "capability": self.capability,
                    "reply": result.reply.to_dict(),
                    "used_harness": result.used_harness,
                    "llm_tokens": result.llm_tokens,
                    "steps": self._trace_steps(result.session_id),
                })
            except Exception as exc:  # noqa: BLE001
                await self._publish_error(msg.data, exc)
            finally:
                await self._bus.ack(self._tasks_stream, self._group, msg.message_id)

    def _trace_steps(self, session_id: str) -> list[dict]:
        if not session_id:
            return []
        try:
            session = self._recorder.get(session_id)
        except KeyError:
            return []
        return [
            {"tool": s.tool, "status": "done" if s.success else "failed",
             "duration_ms": round(s.duration_ms, 2)}
            for s in session.steps
        ]

    async def _publish_error(self, task: dict, exc: Exception) -> None:
        env_d = (task or {}).get("envelope", {})
        reply = OutboundEnvelope(
            in_reply_to=env_d.get("message_id", ""),
            target_channel=env_d.get("source_channel", ""),
            target_address=env_d.get("source_address", ""),
            payload={"text": f"{self.capability} agent error: {exc}"},
        )
        with contextlib.suppress(Exception):
            await self._bus.publish(self._results, {
                "task_id": (task or {}).get("task_id"),
                "capability": self.capability,
                "reply": reply.to_dict(),
                "used_harness": False, "llm_tokens": 0, "steps": [],
            })


# --------------------------------------------------------------------------
# Channel client (producer + reply consumer) — shared by CLI and frontend
# --------------------------------------------------------------------------


@dataclass
class ChannelReply:
    text: str
    harness_hit: str | None
    raw: OutboundEnvelope


class ChannelClient:
    """One channel surface: publish to inbound, await correlated replies.

    The CLI and the browser frontend each construct one of these with their
    own ``name``/``trust``. ``request`` is the synchronous-feeling call both
    surfaces use; the path through the bus is identical for either.
    """

    def __init__(
        self,
        bus: QueueBus,
        name: str,
        trust: TrustLevel,
        *,
        inbound_stream: str = STREAM_INBOUND,
        replies_stream: str = STREAM_REPLIES,
    ) -> None:
        self._bus = bus
        self.name = name
        self.trust = trust
        self._inbound = inbound_stream
        self._replies = replies_stream
        self._pending: dict[str, asyncio.Future] = {}
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(
                self._consume_replies(), name=f"channel-{self.name}"
            )

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def submit(self, text: str, address: str = "user") -> str:
        env = InboundEnvelope(
            source_channel=self.name,
            source_address=address,
            trust=self.trust,
            payload={"text": text},
        )
        await self._bus.publish(self._inbound, env.to_dict())
        return env.message_id

    async def request(
        self, text: str, address: str = "user", timeout: float = 120.0
    ) -> ChannelReply:
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        msg_id = await self._submit_tracked(text, address, fut)
        try:
            reply: OutboundEnvelope = await asyncio.wait_for(fut, timeout)
        finally:
            self._pending.pop(msg_id, None)
        return ChannelReply(
            text=reply.payload.get("text", ""),
            harness_hit=reply.harness_hit,
            raw=reply,
        )

    async def _submit_tracked(
        self, text: str, address: str, fut: asyncio.Future
    ) -> str:
        env = InboundEnvelope(
            source_channel=self.name,
            source_address=address,
            trust=self.trust,
            payload={"text": text},
        )
        self._pending[env.message_id] = fut
        await self._bus.publish(self._inbound, env.to_dict())
        return env.message_id

    async def _consume_replies(self) -> None:
        group = f"channel-{self.name}"
        async for msg in self._bus.consume(self._replies, group, self.name):
            try:
                reply = OutboundEnvelope.from_dict(msg.data)
                if reply.target_channel == self.name:
                    fut = self._pending.get(reply.in_reply_to)
                    if fut is not None and not fut.done():
                        fut.set_result(reply)
            finally:
                await self._bus.ack(self._replies, group, msg.message_id)
