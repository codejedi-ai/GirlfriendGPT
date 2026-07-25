"""Local WebSocket hub: frontend ↔ backend so companions can check up / voice-call.

Protocol (JSON):

  Client → server
    {"type":"hello","client_session_id":"..."}
    {"type":"talk_state","live":true|false}
    {"type":"ping"}

  Server → client
    {"type":"welcome",...}
    {"type":"pong",...}
    {"type":"voice_call",...,"message":"is checking up on you","greeting_context":"reminder_call"}
    {"type":"agent_reach",...}  # banner only

``POST /api/agent/reach`` (purpose=checkup) and the checkup loop ring idle browsers.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger("local-events")


class ReachRequest(BaseModel):
    agent_id: str
    agent_name: str | None = None
    message: str | None = None
    client_session_id: str | None = None
    # voice_call → UI opens talk (+ auto-starts LiveKit when auto_answer)
    # notify → banner only (user taps Answer)
    mode: Literal["voice_call", "notify"] = "voice_call"
    auto_answer: bool = True
    # Passed through to POST /api/token so the worker greets as a check-up.
    greeting_context: str = "reminder_call"
    purpose: str | None = "checkup"


@dataclass
class _Client:
    ws: WebSocket
    client_session_id: str | None = None
    connected_at: float = field(default_factory=time.time)
    talk_live: bool = False
    last_checkup_at: float | None = None


class LocalEventHub:
    def __init__(self) -> None:
        self._clients: dict[int, _Client] = {}
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> _Client:
        await ws.accept()
        client = _Client(ws=ws)
        async with self._lock:
            self._clients[id(ws)] = client
        logger.info("ws connected clients=%d", len(self._clients))
        return client

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.pop(id(ws), None)
        logger.info("ws disconnected clients=%d", len(self._clients))

    def snapshot_clients(self) -> list[_Client]:
        return list(self._clients.values())

    async def bind_session(self, ws: WebSocket, client_session_id: str) -> None:
        async with self._lock:
            client = self._clients.get(id(ws))
            if client is not None:
                client.client_session_id = client_session_id.strip() or None

    async def set_talk_live(self, ws: WebSocket, live: bool) -> None:
        async with self._lock:
            client = self._clients.get(id(ws))
            if client is not None:
                client.talk_live = bool(live)

    async def broadcast(
        self,
        event: dict[str, Any],
        *,
        client_session_id: str | None = None,
    ) -> int:
        payload = {**event, "ts": time.time()}
        dead: list[WebSocket] = []
        async with self._lock:
            targets = list(self._clients.values())
        delivered = 0
        for client in targets:
            if client_session_id:
                if not client.client_session_id:
                    continue
                if client.client_session_id != client_session_id:
                    continue
            try:
                await client.ws.send_json(payload)
                delivered += 1
            except Exception:  # noqa: BLE001
                dead.append(client.ws)
        for ws in dead:
            await self.disconnect(ws)
        return delivered


hub = LocalEventHub()


async def events_websocket(websocket: WebSocket) -> None:
    client = await hub.connect(websocket)
    try:
        await websocket.send_json(
            {"type": "welcome", "ts": time.time(), "message": "local events connected"}
        )
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw) if raw.strip().startswith("{") else {"type": "ping"}
            except json.JSONDecodeError:
                msg = {"type": "ping"}
            kind = str(msg.get("type") or "").strip().lower()
            if kind == "hello":
                sid = str(msg.get("client_session_id") or "").strip()
                if sid:
                    await hub.bind_session(websocket, sid)
                    client.client_session_id = sid
                await websocket.send_json(
                    {
                        "type": "welcome",
                        "client_session_id": client.client_session_id,
                        "ts": time.time(),
                    }
                )
            elif kind == "talk_state":
                await hub.set_talk_live(websocket, bool(msg.get("live")))
            elif kind in {"ping", "keepalive"}:
                await websocket.send_json({"type": "pong", "ts": time.time()})
            # ignore other client messages
    except WebSocketDisconnect:
        await hub.disconnect(websocket)
    except Exception:  # noqa: BLE001
        await hub.disconnect(websocket)


async def publish_agent_reach(body: ReachRequest) -> dict[str, Any]:
    mode = body.mode if body.mode in {"voice_call", "notify"} else "voice_call"
    auto_answer = bool(body.auto_answer) if mode == "voice_call" else False
    event_type = "voice_call" if mode == "voice_call" else "agent_reach"
    purpose = (body.purpose or "").strip() or "checkup"
    greeting_context = (body.greeting_context or "").strip() or (
        "reminder_call" if purpose == "checkup" else "web_session"
    )
    default_msg = (
        "is checking up on you"
        if purpose == "checkup"
        else ("wants to talk with you" if mode == "voice_call" else "is reaching out")
    )
    event = {
        "type": event_type,
        "agent_id": body.agent_id.strip(),
        "agent_name": (body.agent_name or "").strip() or "Companion",
        "message": (body.message or "").strip() or default_msg,
        "client_session_id": (body.client_session_id or "").strip() or None,
        "auto_answer": auto_answer,
        "mode": mode,
        "greeting_context": greeting_context,
        "purpose": purpose,
    }
    delivered = await hub.broadcast(
        event,
        client_session_id=event["client_session_id"],
    )
    # If targeted and nobody matched, fall back to broadcast all browsers.
    if event["client_session_id"] and delivered == 0:
        delivered = await hub.broadcast({**event, "client_session_id": None})
    logger.info(
        "%s agent=%s name=%s auto_answer=%s delivered=%d",
        event_type,
        event["agent_id"],
        event["agent_name"],
        auto_answer,
        delivered,
    )
    return {"ok": True, "delivered": delivered, "event": event}
