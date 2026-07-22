"""Gateway integration for the self-improving agent harness.

Mounts the harness onto the main ConfigClaw FastAPI gateway so you can drive
the cold -> reflect -> warm loop from the browser instead of only the CLI.

Surfaces (all under ``/api/v1/harness``):
  POST /messages   — submit an intent; returns the reply + cold/warm telemetry
  WS   /ws         — same, streaming (one JSON frame per reply)
  GET  /state      — promoted workflows, generated tools, trace count
  POST /reset      — wipe learned state (workflows/generated/traces) for a
                     clean cold-start demo against the persistent store

The user-facing UI is the app/frontend React app (served at /), not here.

Messages are published to the queue and served by a DispatcherWorker, which
runs ``reflect`` after every message, so the 3rd identical ``scrape`` intent
gets promoted and the 4th warm-hits the generated tool.

The harness keeps its own backings (Redis/MinIO/Postgres via HARNESS_* env,
see app/agents/harness/factory.py). Building it is best-effort: if a backing
is down the factory falls back to in-memory, so this never blocks gateway boot.
"""

from __future__ import annotations

import asyncio

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from harness.factory import HarnessConfig, build_harness
from harness.envelope import TrustLevel
from harness.runtime import ChannelClient, DispatcherAgent, TaskAgent

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/harness", tags=["harness"])

# Module-level singletons for the multi-agent runtime. The browser and the CLI
# are both channels: they publish to the queue, the DispatcherAgent routes to a
# TaskAgent, and the result comes back through the queue — same path for either.
_bundle = None
_dispatcher_agent: DispatcherAgent | None = None
_scraper_agent: TaskAgent | None = None
_http_client: ChannelClient | None = None   # admin console (HTTP POST)
_ws_client: ChannelClient | None = None      # browser terminal (WebSocket)
_lock = asyncio.Lock()


async def _ensure():
    global _bundle, _dispatcher_agent, _scraper_agent, _http_client, _ws_client
    if _bundle is not None:
        return
    async with _lock:
        if _bundle is not None:
            return
        bundle = await build_harness(HarnessConfig.from_env())
        dispatcher_agent = DispatcherAgent(
            bundle.bus,
            store=bundle.store,
            registry=bundle.registry,
            tools=bundle.tools,
            reflect_min_hits=3,
        )
        scraper_agent = TaskAgent(
            bundle.bus, bundle.dispatcher, bundle.recorder, capability="scraper",
        )
        dispatcher_agent.start()
        scraper_agent.start()
        http_client = ChannelClient(bundle.bus, name="fastapi", trust=TrustLevel.ADMIN)
        ws_client = ChannelClient(bundle.bus, name="browser-term", trust=TrustLevel.USER)
        http_client.start()
        ws_client.start()
        # Give the redis consumer groups a moment to attach before first use.
        await asyncio.sleep(0.2)
        _bundle, _dispatcher_agent, _scraper_agent, _http_client, _ws_client = (
            bundle, dispatcher_agent, scraper_agent, http_client, ws_client
        )
        logger.info(
            "harness_runtime_started",
            bus=bundle.mode_report.bus,
            store=bundle.mode_report.store,
            registry=bundle.mode_report.registry_index,
            llm=bundle.mode_report.llm_policy,
        )


async def _get_bundle():
    await _ensure()
    return _bundle


def _classify(text: str, harness_hit) -> str:
    """Label the reply for the UI: warm replay, cold LLM answer, or declined."""
    if harness_hit:
        return "warm"
    if text.strip().startswith("Price:"):
        return "cold"
    return "declined"


async def _handle(text: str, client: ChannelClient, address: str) -> dict:
    """Publish to the queue via a channel client; await the worker's reply."""
    await _ensure()
    reply = await client.request(text, address=address)
    kind = _classify(reply.text, reply.harness_hit)
    # Reflection runs inside the worker after it replies; surface its latest
    # promotion (may lag the triggering turn by one — the state panel is truth).
    refl = _dispatcher_agent.last_reflection if _dispatcher_agent else None
    return {
        "text": reply.text,
        "kind": kind,
        "harness_hit": reply.harness_hit,
        "used_harness": reply.harness_hit is not None,
        "promoted": list(getattr(refl, "workflows_activated", []) or []),
        "generated": list(getattr(refl, "generated_tools_created", []) or []),
    }


@router.post("/messages")
async def post_message(payload: dict) -> dict:
    """Submit an intent over HTTP -> queue -> dispatcher. Admin trust."""
    text = (payload or {}).get("text", "")
    if not text.strip():
        return {"error": "empty intent"}
    await _ensure()
    return await _handle(text, _http_client, address="http-console")


@router.get("/state")
async def state() -> dict:
    bundle = await _get_bundle()
    workflows = [
        {
            "id": w.id,
            "status": w.status.value,
            "steps": len(w.steps),
            "hits": w.hits,
        }
        for w in bundle.registry.list_workflows()
    ]
    traces = sum(1 for k in bundle.store.list("traces") if k.endswith(".jsonl"))
    return {
        "mode": {
            "bus": bundle.mode_report.bus,
            "store": bundle.mode_report.store,
            "registry": bundle.mode_report.registry_index,
            "llm": bundle.mode_report.llm_policy,
            "scraper": bundle.mode_report.scraper,
        },
        "workflows": workflows,
        "generated_tools": list(bundle.registry._generated.keys()),
        "traces": traces,
        "worker": {
            "dispatched": _dispatcher_agent.dispatched if _dispatcher_agent else 0,
            "replied": _dispatcher_agent.replied if _dispatcher_agent else 0,
            "tasks_handled": _scraper_agent.handled if _scraper_agent else 0,
        },
    }


@router.post("/reset")
async def reset() -> dict:
    """Wipe learned state so the next intent is a genuine cold start.

    Clears workflows/generated/traces from the store and resets the in-memory
    registry. The worker + channel clients keep running (they share the same
    registry, so they immediately see the cleared state).
    """
    bundle = await _get_bundle()
    removed = 0
    for prefix in ("workflows", "generated", "traces"):
        for key in list(bundle.store.list(prefix)):
            bundle.store.delete(key)
            removed += 1
    bundle.registry.reset()
    logger.info("harness_reset", removed=removed)
    return {"reset": True, "removed_objects": removed}


@router.websocket("/ws")
async def ws(websocket: WebSocket) -> None:
    """Streaming chat over queue -> dispatcher. User trust (browser surface)."""
    await websocket.accept()
    await _ensure()
    addr = f"ws-{id(websocket) & 0xffff}"
    try:
        while True:
            text = await websocket.receive_text()
            if not text.strip():
                continue
            try:
                payload = await _handle(text, _ws_client, address=addr)
            except Exception as exc:  # noqa: BLE001
                payload = {"text": f"error: {exc}", "kind": "error"}
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        return


async def start_harness(app) -> None:
    """Start the queue-driven runtime on gateway startup (best-effort)."""
    try:
        await _ensure()
    except Exception as exc:  # noqa: BLE001
        logger.warning("harness_start_failed", error=str(exc))


async def stop_harness(app) -> None:
    """Tear down agents + clients + backings on shutdown (best-effort)."""
    global _bundle, _dispatcher_agent, _scraper_agent, _http_client, _ws_client
    for comp in (_http_client, _ws_client, _scraper_agent, _dispatcher_agent):
        if comp is not None:
            try:
                await comp.stop()
            except Exception:  # noqa: BLE001
                pass
    if _bundle is not None:
        try:
            await _bundle.shutdown()
        except Exception:  # noqa: BLE001
            pass
    _bundle = _dispatcher_agent = _scraper_agent = _http_client = _ws_client = None
