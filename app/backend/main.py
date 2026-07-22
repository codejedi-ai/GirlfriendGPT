"""GirlfriendGPT backend API (app/backend).

Traffic model (locked)::

    Frontend  --POST /api/token-->  this backend  → { token, url, reused, … }
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
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from companions import list_companions
from livekit_token import (
    TokenRequest,
    TokenResponse,
    agent_worker_name,
    build_token_payload,
    default_agent_id,
    livekit_url_for_browser,
)
from voice_sessions import connect_voice_session

_BACKEND_DIR = Path(__file__).resolve().parent
_STATIC_DIR = _BACKEND_DIR / "static"
_AGENT_TALK_STATIC = _BACKEND_DIR.parent / "agent" / "talk" / "static"

load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_BACKEND_DIR.parent / "agent" / ".env")
load_dotenv(_BACKEND_DIR.parents[1] / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(title="GirlfriendGPT Backend", version="0.1.0")
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


@app.post("/api/token", response_model=TokenResponse)
@app.post("/api/connect", response_model=TokenResponse)
async def issue_token(body: TokenRequest | None = None) -> TokenResponse:
    """Mint JWT; reuse active agent room when possible (no second dispatch)."""
    req = body or TokenRequest()
    client_session_id = (req.client_session_id or "").strip() or str(uuid.uuid4())
    agent_id = (req.agent_id or "").strip() or default_agent_id()

    # Explicit room override (tests / debug) — skip session registry.
    if (req.room or "").strip():
        try:
            payload = build_token_payload(
                room=req.room,
                identity=req.identity,
                name=req.name,
                agent_id=agent_id,
                greeting_context=req.greeting_context,
                dispatch_agent=True,
            )
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        payload.client_session_id = client_session_id
        payload.reused = False
        payload.agent_state = "starting"
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
        "token room=%s identity=%s agent=%s reused=%s state=%s",
        payload.room,
        payload.identity,
        payload.agent_id,
        payload.reused,
        payload.agent_state,
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
