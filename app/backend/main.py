"""GirlfriendGPT backend API (app/backend).

Traffic model (locked)::

    Frontend  --POST /api/token-->  this backend  → { token, url, reused, … }
    Frontend  --WS /api/ws/events->  this backend  → voice_call / check-up ring
    Frontend  --Room.connect----->  LiveKit SFU   → WebRTC

Run::

    cd app/backend
    uv sync
    uv run python main.py
"""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from checkup import checkup_loop, run_checkup_once
from caller_memory import (
    CallerMemoryUpdate,
    apply_update,
    load_memory,
    memory_to_dict,
    upsert_display_name,
)
from companions import list_companions
from livekit_token import (
    TokenRequest,
    TokenResponse,
    agent_worker_name,
    build_token_payload,
    default_agent_id,
    livekit_url_for_browser,
)
from local_events import ReachRequest, events_websocket, publish_agent_reach
from voice_sessions import (
    connect_voice_session,
    list_mints,
    list_rooms,
    list_sessions,
    record_mint_from_payload,
)

_BACKEND_DIR = Path(__file__).resolve().parent
_STATIC_DIR = _BACKEND_DIR / "static"
_AGENT_TALK_STATIC = _BACKEND_DIR.parent / "agent" / "talk" / "static"

load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_BACKEND_DIR.parent / "agent" / ".env")
load_dotenv(_BACKEND_DIR.parents[1] / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import asyncio

    task = asyncio.create_task(checkup_loop())
    logger.info("started companion checkup loop")
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="GirlfriendGPT Backend", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _talk_index() -> Path | None:
    for candidate in (
        _STATIC_DIR / "index.html",
        _AGENT_TALK_STATIC / "index.html",
    ):
        if candidate.is_file():
            return candidate
    return None


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "app/backend",
        "livekit_url": livekit_url_for_browser(),
        "agent_name": agent_worker_name(),
        "default_agent_id": default_agent_id(),
    }


@app.get("/api/companions")
def companions() -> dict[str, Any]:
    """Character list for the Talk UI left bar (templates + personas)."""
    items = list_companions()
    return {"companions": items, "count": len(items)}


@app.websocket("/api/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    """Browser listens here so companions can check up / voice-call the user."""
    await events_websocket(websocket)


@app.post("/api/agent/reach")
async def agent_reach(body: ReachRequest) -> dict[str, Any]:
    """Agent → user. Default purpose=checkup (warm check-up voice call)."""
    return await publish_agent_reach(body)


@app.post("/api/agent/checkup")
async def agent_checkup() -> dict[str, Any]:
    """Force a check-up tick (rings idle browsers that are due)."""
    results = await run_checkup_once()
    return {"ok": True, "rang": len(results), "results": results}


@app.get("/api/voice-sessions")
def voice_sessions() -> dict[str, Any]:
    """Tracked (client, agent) → room mappings and last-token expiry state."""
    items = list_sessions()
    return {"sessions": items, "count": len(items)}


@app.get("/api/rooms")
def rooms() -> dict[str, Any]:
    """All rooms that have received a minted token + last token expiry state."""
    items = list_rooms()
    return {"rooms": items, "count": len(items)}


@app.get("/api/token-mints")
def token_mints(limit: int = 100) -> dict[str, Any]:
    """Mint ledger: every JWT mint with room, issued_at, expires_at, expiry_state."""
    items = list_mints(limit=max(1, min(limit, 1000)))
    return {"mints": items, "count": len(items)}


@app.get("/api/caller-memory/{client_session_id}")
def get_caller_memory(client_session_id: str) -> dict[str, Any]:
    """Durable written-down memory for a browser session (reload on cold connect)."""
    mem = load_memory(client_session_id)
    return {"ok": True, "memory": memory_to_dict(mem)}


@app.put("/api/caller-memory/{client_session_id}")
def put_caller_memory(
    client_session_id: str, body: CallerMemoryUpdate
) -> dict[str, Any]:
    """Update name / notes / summary the companion should not forget."""
    mem = apply_update(client_session_id, body)
    return {"ok": True, "memory": memory_to_dict(mem)}


@app.post("/api/token", response_model=TokenResponse)
@app.post("/api/connect", response_model=TokenResponse)
async def issue_token(body: TokenRequest | None = None) -> TokenResponse:
    """Mint JWT; reuse active agent room when possible (no second dispatch)."""
    req = body or TokenRequest()
    client_session_id = (req.client_session_id or "").strip() or str(uuid.uuid4())
    agent_id = (req.agent_id or "").strip() or default_agent_id()
    caller_name = (req.name or "").strip()
    if caller_name and caller_name != "You":
        upsert_display_name(client_session_id, caller_name)

    # Explicit room override (tests / debug) — still log mint + room registry.
    if (req.room or "").strip():
        try:
            payload = build_token_payload(
                room=req.room,
                identity=req.identity,
                name=req.name,
                agent_id=agent_id,
                greeting_context=req.greeting_context,
                dispatch_agent=True,
                client_session_id=client_session_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        payload.client_session_id = client_session_id
        payload.reused = False
        payload.agent_state = "starting"
        record_mint_from_payload(
            payload,
            client_session_id=client_session_id,
            reused=False,
            dispatch_agent=True,
            session=None,
        )
        return payload

    try:
        result = await connect_voice_session(
            client_session_id=client_session_id,
            agent_id=agent_id,
            mint_token=build_token_payload,
            greeting_context=req.greeting_context,
            identity=req.identity,
            name=req.name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload: TokenResponse = result["payload"]
    payload.reused = bool(result["reused"])
    payload.agent_state = str(result["agent_state"])
    payload.agent_participant_id = result.get("agent_participant_id")
    payload.client_session_id = client_session_id
    logger.info(
        "token room=%s identity=%s agent=%s reused=%s state=%s token_id=%s expiry=%s",
        payload.room,
        payload.identity,
        payload.agent_id,
        payload.reused,
        payload.agent_state,
        payload.token_id,
        payload.expiry_state,
    )
    return payload


@app.get("/")
def index() -> FileResponse:
    path = _talk_index()
    if path is None:
        raise HTTPException(
            status_code=404,
            detail="Talk UI missing (app/backend/static or app/agent/talk/static)",
        )
    return FileResponse(path)


_static_root = _STATIC_DIR if _STATIC_DIR.is_dir() else _AGENT_TALK_STATIC
if _static_root.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_root)), name="static")


def main() -> None:
    import uvicorn

    host = (os.getenv("BACKEND_HOST") or os.getenv("TALK_HOST") or "0.0.0.0").strip()
    port = int((os.getenv("BACKEND_PORT") or os.getenv("TALK_PORT") or "8080").strip())
    uvicorn.run("main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
