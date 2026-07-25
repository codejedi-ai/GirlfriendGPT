"""Mint LiveKit access tokens for the voice talk frontend.

Backend owns session lifecycle (see ``voice_sessions``). Frontend calls
``POST /api/token`` with ``client_session_id`` + ``agent_id``, then connects
to LiveKit with the returned ``token`` + ``url``.

Every mint is logged with room + expiry (``voice_sessions`` ledger).
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import timedelta
from typing import Any

from livekit import api
from pydantic import BaseModel, Field

ELLA_AGENT_ID = "e11a0000-0000-4000-8000-000000000001"
# Must match AccessToken.with_ttl below — ledger uses this for expiry_state.
TOKEN_TTL_SECONDS = int(
    (os.getenv("LIVEKIT_TOKEN_TTL_SECONDS") or str(2 * 60 * 60)).strip() or str(2 * 60 * 60)
)


class TokenRequest(BaseModel):
    room: str | None = None
    identity: str | None = None
    name: str | None = None
    agent_id: str | None = None
    client_session_id: str | None = None
    greeting_context: str = "web_session"


class TokenResponse(BaseModel):
    token: str
    url: str
    room: str
    identity: str
    agent_id: str
    agent_name: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    reused: bool = False
    agent_state: str = "starting"
    agent_participant_id: str | None = None
    client_session_id: str | None = None
    token_id: str | None = None
    issued_at: float | None = None
    expires_at: float | None = None
    ttl_seconds: int | None = None
    expiry_state: str = "active"  # active | expired (at mint time always active)


def livekit_url_for_browser() -> str:
    url = (os.getenv("LIVEKIT_URL") or "ws://127.0.0.1:7880").strip()
    if url.startswith("https://"):
        return "wss://" + url.removeprefix("https://")
    if url.startswith("http://"):
        return "ws://" + url.removeprefix("http://")
    return url


def api_key() -> str:
    return (os.getenv("LIVEKIT_API_KEY") or "devkey").strip()


def api_secret() -> str:
    return (os.getenv("LIVEKIT_API_SECRET") or "secret").strip()


def agent_worker_name() -> str:
    return (
        os.getenv("LIVEKIT_AGENT_NAME") or os.getenv("AGENT_NAME") or "AI-LiveKit-Agent"
    ).strip()


def default_agent_id() -> str:
    return (
        os.getenv("GIRLFRIENDGPT_AGENT_ID") or os.getenv("ALI_AGENT_ID") or ELLA_AGENT_ID
    ).strip()


def token_ttl_seconds() -> int:
    raw = (os.getenv("LIVEKIT_TOKEN_TTL_SECONDS") or str(TOKEN_TTL_SECONDS)).strip()
    try:
        return max(60, int(raw))
    except ValueError:
        return max(60, TOKEN_TTL_SECONDS)


def build_token_payload(
    *,
    room: str | None = None,
    identity: str | None = None,
    name: str | None = None,
    agent_id: str | None = None,
    greeting_context: str = "web_session",
    dispatch_agent: bool = True,
    client_session_id: str | None = None,
) -> TokenResponse:
    """Build JWT. When *dispatch_agent* is False, skip RoomAgentDispatch (reconnect)."""
    key = api_key()
    secret = api_secret()
    if not key or not secret:
        raise ValueError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET are required")

    room_name = (room or "").strip() or f"talk-{uuid.uuid4().hex[:8]}"
    user_identity = (identity or "").strip() or f"user-{uuid.uuid4().hex[:8]}"
    display = (name or "").strip() or "You"
    aid = (agent_id or "").strip() or default_agent_id()
    worker = agent_worker_name()
    csid = (client_session_id or "").strip() or None
    ttl = token_ttl_seconds()
    issued_at = time.time()
    expires_at = issued_at + ttl
    token_id = uuid.uuid4().hex[:16]
    meta: dict[str, Any] = {
        "agent_id": aid,
        "greeting_context": greeting_context or "web_session",
        "caller_name": display if display != "You" else "",
        "token_id": token_id,
        "issued_at": issued_at,
        "expires_at": expires_at,
    }
    if csid:
        meta["client_session_id"] = csid
    meta_json = json.dumps(meta)

    builder = (
        api.AccessToken(api_key=key, api_secret=secret)
        .with_identity(user_identity)
        .with_name(display)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
                can_publish_sources=["microphone", "camera", "screen_share"],
            )
        )
        .with_ttl(timedelta(seconds=ttl))
    )
    if dispatch_agent:
        builder = builder.with_room_config(
            api.RoomConfiguration(
                agents=[
                    api.RoomAgentDispatch(
                        agent_name=worker,
                        metadata=meta_json,
                    )
                ],
            ),
        )

    return TokenResponse(
        token=builder.to_jwt(),
        url=livekit_url_for_browser(),
        room=room_name,
        identity=user_identity,
        agent_id=aid,
        agent_name=worker,
        metadata=meta,
        token_id=token_id,
        issued_at=issued_at,
        expires_at=expires_at,
        ttl_seconds=ttl,
        expiry_state="active",
    )
