"""In-memory voice session registry — reconnect to an active agent room.

Soft leave: human disconnects; session stays up for ``VOICE_SESSION_IDLE_SECONDS``
(default 30 minutes). Hard end: idle expiry deletes the LiveKit room and registry
entry so the next connect cold-starts with agent dispatch.
"""

from __future__ import annotations

import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from livekit import api

from companions import list_companions

logger = logging.getLogger("voice-sessions")

VOICE_SESSION_IDLE_SECONDS = int(
    (os.getenv("VOICE_SESSION_IDLE_SECONDS") or "1800").strip() or "1800"
)


@dataclass
class VoiceSession:
    client_session_id: str
    agent_id: str
    room_id: str
    agent_participant_id: str
    last_human_at: float = field(default_factory=time.time)
    agent_state: str = "starting"  # starting | running


_sessions: dict[tuple[str, str], VoiceSession] = {}


def _key(client_session_id: str, agent_id: str) -> tuple[str, str]:
    return (client_session_id.strip(), agent_id.strip())


def idle_seconds() -> int:
    raw = (os.getenv("VOICE_SESSION_IDLE_SECONDS") or str(VOICE_SESSION_IDLE_SECONDS)).strip()
    try:
        return max(60, int(raw))
    except ValueError:
        return max(60, VOICE_SESSION_IDLE_SECONDS)


def clear_sessions() -> None:
    """Test helper."""
    _sessions.clear()


def get_session(client_session_id: str, agent_id: str) -> VoiceSession | None:
    return _sessions.get(_key(client_session_id, agent_id))


def upsert_session(session: VoiceSession) -> VoiceSession:
    _sessions[_key(session.client_session_id, session.agent_id)] = session
    return session


def drop_session(client_session_id: str, agent_id: str) -> None:
    _sessions.pop(_key(client_session_id, agent_id), None)


def touch_human(client_session_id: str, agent_id: str) -> None:
    sess = get_session(client_session_id, agent_id)
    if sess is not None:
        sess.last_human_at = time.time()


def room_id_for(client_session_id: str, agent_id: str) -> str:
    """Stable room name for a (client, agent) session."""
    short_client = re.sub(r"[^a-zA-Z0-9]", "", client_session_id)[:8] or uuid.uuid4().hex[:8]
    short_agent = re.sub(r"[^a-zA-Z0-9]", "", agent_id.replace("-", ""))[:8] or "agent"
    return f"voice-{short_client.lower()}-{short_agent.lower()}"


def human_identity_for(client_session_id: str) -> str:
    short = re.sub(r"[^a-zA-Z0-9]", "", client_session_id)[:12] or uuid.uuid4().hex[:8]
    return f"user-{short.lower()}"


def resolve_agent_participant_id(agent_id: str) -> str:
    """Load permanent participant_id from companions catalog / personas."""
    aid = (agent_id or "").strip()
    for card in list_companions():
        if str(card.get("agent_id") or "").strip() == aid:
            pid = str(card.get("participant_id") or "").strip()
            if pid:
                return pid
            name = str(card.get("name") or "agent").strip()
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "agent"
            short = aid.replace("-", "")[:8] or "00000000"
            return f"agent-{slug}-{short}"
    short = aid.replace("-", "")[:8] or uuid.uuid4().hex[:8]
    return f"agent-companion-{short}"


def livekit_http_url() -> str:
    url = (os.getenv("LIVEKIT_URL") or "ws://127.0.0.1:7880").strip()
    if url.startswith("wss://"):
        return "https://" + url.removeprefix("wss://")
    if url.startswith("ws://"):
        return "http://" + url.removeprefix("ws://")
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return "http://" + url


def _api_key() -> str:
    return (os.getenv("LIVEKIT_API_KEY") or "devkey").strip()


def _api_secret() -> str:
    return (os.getenv("LIVEKIT_API_SECRET") or "secret").strip()


async def list_room_identities(room_id: str) -> list[str]:
    """Return participant identities in *room_id*, or [] if room missing."""
    try:
        async with api.LiveKitAPI(livekit_http_url(), _api_key(), _api_secret()) as lk:
            res = await lk.room.list_participants(
                api.ListParticipantsRequest(room=room_id)
            )
    except Exception as exc:  # noqa: BLE001
        logger.info("list_participants room=%s failed: %s", room_id, exc)
        return []
    out: list[str] = []
    for p in getattr(res, "participants", None) or []:
        ident = str(getattr(p, "identity", "") or "").strip()
        if ident:
            out.append(ident)
    return out


async def delete_livekit_room(room_id: str) -> None:
    try:
        async with api.LiveKitAPI(livekit_http_url(), _api_key(), _api_secret()) as lk:
            await lk.room.delete_room(api.DeleteRoomRequest(room=room_id))
        logger.info("Hard-ended LiveKit room=%s", room_id)
    except Exception as exc:  # noqa: BLE001
        logger.info("delete_room room=%s ignored: %s", room_id, exc)


def _is_human_identity(identity: str) -> bool:
    low = identity.lower()
    if low.startswith("agent-") or low.startswith("agent_"):
        return False
    # LiveKit auto agent jobs look like agent-AJ_…
    return True


async def hard_end_session(session: VoiceSession) -> None:
    drop_session(session.client_session_id, session.agent_id)
    await delete_livekit_room(session.room_id)


async def sweep_idle_sessions(*, now: float | None = None) -> list[str]:
    """Hard-end sessions idle past the timeout with no human in the room."""
    ts = now if now is not None else time.time()
    limit = idle_seconds()
    ended: list[str] = []
    for sess in list(_sessions.values()):
        if ts - sess.last_human_at < limit:
            continue
        identities = await list_room_identities(sess.room_id)
        humans = [i for i in identities if _is_human_identity(i)]
        if humans:
            sess.last_human_at = ts
            continue
        await hard_end_session(sess)
        ended.append(sess.room_id)
    return ended


async def connect_voice_session(
    *,
    client_session_id: str,
    agent_id: str,
    mint_token: Callable[..., Any],
    greeting_context: str = "web_session",
    identity: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """Resolve reuse vs dispatch and return token payload fields + session flags.

    *mint_token* is ``build_token_payload``-compatible callable returning an object
    with ``token``, ``url``, ``room``, ``identity``, ``agent_id``, ``agent_name``,
    ``metadata``.
    """
    await sweep_idle_sessions()

    csid = (client_session_id or "").strip()
    if not csid:
        raise ValueError("client_session_id is required")
    aid = (agent_id or "").strip()
    if not aid:
        raise ValueError("agent_id is required")

    agent_pid = resolve_agent_participant_id(aid)
    human_id = (identity or "").strip() or human_identity_for(csid)
    display = (name or "").strip() or "You"

    existing = get_session(csid, aid)
    room = existing.room_id if existing else room_id_for(csid, aid)

    identities = await list_room_identities(room)
    agent_present = agent_pid in identities

    if agent_present:
        sess = existing or VoiceSession(
            client_session_id=csid,
            agent_id=aid,
            room_id=room,
            agent_participant_id=agent_pid,
            last_human_at=time.time(),
            agent_state="running",
        )
        sess.agent_state = "running"
        sess.last_human_at = time.time()
        upsert_session(sess)
        payload = mint_token(
            room=room,
            identity=human_id,
            name=display,
            agent_id=aid,
            greeting_context=greeting_context,
            dispatch_agent=False,
        )
        return {
            "payload": payload,
            "reused": True,
            "agent_state": "running",
            "agent_participant_id": agent_pid,
        }

    # Cold start or agent gone — keep stable room id, dispatch agent.
    sess = VoiceSession(
        client_session_id=csid,
        agent_id=aid,
        room_id=room,
        agent_participant_id=agent_pid,
        last_human_at=time.time(),
        agent_state="starting",
    )
    upsert_session(sess)
    payload = mint_token(
        room=room,
        identity=human_id,
        name=display,
        agent_id=aid,
        greeting_context=greeting_context,
        dispatch_agent=True,
    )
    return {
        "payload": payload,
        "reused": False,
        "agent_state": "starting",
        "agent_participant_id": agent_pid,
    }
