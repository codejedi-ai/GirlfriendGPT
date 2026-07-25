"""In-memory + disk voice session registry — remint tokens into the same room.

Short-term: soft leave keeps the LiveKit room/agent (~30 min idle).
Backend tracks ``(client_session_id, agent_id) → room_id`` so each Connect
mints a **new JWT** for the **same room** — never a random new room.

Persistence: ``~/.gfgpt/voice_sessions.json`` (+ mint ledger) survives backend restarts.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from livekit import api

from companions import list_companions

logger = logging.getLogger("voice-sessions")

VOICE_SESSION_IDLE_SECONDS = int(
    (os.getenv("VOICE_SESSION_IDLE_SECONDS") or "1800").strip() or "1800"
)


def _state_dir() -> Path:
    override = (os.getenv("GFGPT_STATE_DIR") or "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".gfgpt"


def sessions_path() -> Path:
    return _state_dir() / "voice_sessions.json"


def mints_path() -> Path:
    return _state_dir() / "token_mints.jsonl"


@dataclass
class VoiceSession:
    client_session_id: str
    agent_id: str
    room_id: str
    agent_participant_id: str
    last_human_at: float = field(default_factory=time.time)
    agent_state: str = "starting"  # starting | running
    mint_count: int = 0
    last_mint_at: float | None = None
    last_token_id: str | None = None
    last_token_expires_at: float | None = None


@dataclass
class TokenMintRecord:
    """Audit row — every JWT mint: room + issued/expiry (JWT itself not stored)."""

    ts: float
    token_id: str
    client_session_id: str
    agent_id: str
    room_id: str
    identity: str
    reused: bool
    dispatch_agent: bool
    issued_at: float
    expires_at: float
    ttl_seconds: int
    expiry_state: str = "active"  # snapshot at write; recompute on read


@dataclass
class RoomRecord:
    """Every room the backend has minted a token for."""

    room_id: str
    client_session_id: str
    agent_id: str
    first_seen_at: float
    last_mint_at: float
    mint_count: int = 0
    last_token_id: str | None = None
    last_token_expires_at: float | None = None
    last_token_expiry_state: str = "active"


_sessions: dict[tuple[str, str], VoiceSession] = {}
_rooms: dict[str, RoomRecord] = {}
_loaded = False


def _key(client_session_id: str, agent_id: str) -> tuple[str, str]:
    return (client_session_id.strip(), agent_id.strip())


def expiry_state_for(expires_at: float | None, *, now: float | None = None) -> str:
    if expires_at is None:
        return "unknown"
    ts = now if now is not None else time.time()
    return "active" if ts < float(expires_at) else "expired"


def idle_seconds() -> int:
    raw = (os.getenv("VOICE_SESSION_IDLE_SECONDS") or str(VOICE_SESSION_IDLE_SECONDS)).strip()
    try:
        return max(60, int(raw))
    except ValueError:
        return max(60, VOICE_SESSION_IDLE_SECONDS)


def clear_sessions() -> None:
    """Test helper."""
    global _loaded
    _sessions.clear()
    _rooms.clear()
    _loaded = True


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    path = sessions_path()
    if not path.is_file():
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(raw, dict):
        return
    items = raw.get("sessions")
    if isinstance(items, list):
        for row in items:
            if not isinstance(row, dict):
                continue
            csid = str(row.get("client_session_id") or "").strip()
            aid = str(row.get("agent_id") or "").strip()
            room = str(row.get("room_id") or "").strip()
            if not csid or not aid or not room:
                continue
            sess = VoiceSession(
                client_session_id=csid,
                agent_id=aid,
                room_id=room,
                agent_participant_id=str(row.get("agent_participant_id") or "").strip()
                or resolve_agent_participant_id(aid),
                last_human_at=float(row.get("last_human_at") or time.time()),
                agent_state=str(row.get("agent_state") or "starting"),
                mint_count=int(row.get("mint_count") or 0),
                last_mint_at=float(row["last_mint_at"]) if row.get("last_mint_at") else None,
                last_token_id=str(row["last_token_id"]) if row.get("last_token_id") else None,
                last_token_expires_at=(
                    float(row["last_token_expires_at"])
                    if row.get("last_token_expires_at")
                    else None
                ),
            )
            _sessions[_key(csid, aid)] = sess
    rooms = raw.get("rooms")
    if isinstance(rooms, list):
        for row in rooms:
            if not isinstance(row, dict):
                continue
            rid = str(row.get("room_id") or "").strip()
            if not rid:
                continue
            _rooms[rid] = RoomRecord(
                room_id=rid,
                client_session_id=str(row.get("client_session_id") or "").strip(),
                agent_id=str(row.get("agent_id") or "").strip(),
                first_seen_at=float(row.get("first_seen_at") or time.time()),
                last_mint_at=float(row.get("last_mint_at") or time.time()),
                mint_count=int(row.get("mint_count") or 0),
                last_token_id=str(row["last_token_id"]) if row.get("last_token_id") else None,
                last_token_expires_at=(
                    float(row["last_token_expires_at"])
                    if row.get("last_token_expires_at")
                    else None
                ),
                last_token_expiry_state=str(row.get("last_token_expiry_state") or "active"),
            )
    logger.info(
        "Loaded %d voice session(s), %d room(s) from %s",
        len(_sessions),
        len(_rooms),
        path,
    )


def persist_sessions() -> None:
    _ensure_loaded()
    path = sessions_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Refresh expiry_state snapshots before write.
    now = time.time()
    for room in _rooms.values():
        room.last_token_expiry_state = expiry_state_for(
            room.last_token_expires_at, now=now
        )
    payload = {
        "updated_at": now,
        "sessions": [asdict(s) for s in _sessions.values()],
        "rooms": [asdict(r) for r in _rooms.values()],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def append_mint_record(rec: TokenMintRecord) -> None:
    path = mints_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(rec)) + "\n")


def list_sessions() -> list[dict[str, Any]]:
    _ensure_loaded()
    now = time.time()
    out: list[dict[str, Any]] = []
    for s in _sessions.values():
        row = asdict(s)
        row["last_token_expiry_state"] = expiry_state_for(
            s.last_token_expires_at, now=now
        )
        out.append(row)
    return out


def list_rooms() -> list[dict[str, Any]]:
    """All rooms that have received at least one minted token."""
    _ensure_loaded()
    now = time.time()
    out: list[dict[str, Any]] = []
    for r in sorted(_rooms.values(), key=lambda x: x.last_mint_at, reverse=True):
        row = asdict(r)
        row["last_token_expiry_state"] = expiry_state_for(
            r.last_token_expires_at, now=now
        )
        out.append(row)
    return out


def list_mints(*, limit: int = 100) -> list[dict[str, Any]]:
    """Recent token mints with live expiry_state (active | expired)."""
    path = mints_path()
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    now = time.time()
    rows: list[dict[str, Any]] = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        exp = row.get("expires_at")
        row["expiry_state"] = expiry_state_for(
            float(exp) if exp is not None else None, now=now
        )
        rows.append(row)
        if len(rows) >= max(1, limit):
            break
    return rows


def get_session(client_session_id: str, agent_id: str) -> VoiceSession | None:
    _ensure_loaded()
    return _sessions.get(_key(client_session_id, agent_id))


def sessions_for_client(client_session_id: str) -> list[VoiceSession]:
    _ensure_loaded()
    sid = (client_session_id or "").strip()
    if not sid:
        return []
    return [s for (csid, _), s in _sessions.items() if csid == sid]


def upsert_session(session: VoiceSession) -> VoiceSession:
    _ensure_loaded()
    _sessions[_key(session.client_session_id, session.agent_id)] = session
    persist_sessions()
    return session


def drop_session(client_session_id: str, agent_id: str) -> None:
    _ensure_loaded()
    _sessions.pop(_key(client_session_id, agent_id), None)
    persist_sessions()


def touch_human(client_session_id: str, agent_id: str) -> None:
    sess = get_session(client_session_id, agent_id)
    if sess is not None:
        sess.last_human_at = time.time()
        persist_sessions()


def _touch_room(
    *,
    room_id: str,
    client_session_id: str,
    agent_id: str,
    token_id: str,
    expires_at: float,
    now: float,
) -> None:
    existing = _rooms.get(room_id)
    if existing is None:
        _rooms[room_id] = RoomRecord(
            room_id=room_id,
            client_session_id=client_session_id,
            agent_id=agent_id,
            first_seen_at=now,
            last_mint_at=now,
            mint_count=1,
            last_token_id=token_id,
            last_token_expires_at=expires_at,
            last_token_expiry_state=expiry_state_for(expires_at, now=now),
        )
    else:
        existing.last_mint_at = now
        existing.mint_count = int(existing.mint_count or 0) + 1
        existing.last_token_id = token_id
        existing.last_token_expires_at = expires_at
        existing.last_token_expiry_state = expiry_state_for(expires_at, now=now)
        existing.client_session_id = client_session_id or existing.client_session_id
        existing.agent_id = agent_id or existing.agent_id


def record_token_mint(
    *,
    client_session_id: str,
    agent_id: str,
    room_id: str,
    identity: str,
    reused: bool,
    dispatch_agent: bool,
    token_id: str,
    issued_at: float,
    expires_at: float,
    ttl_seconds: int,
    session: VoiceSession | None = None,
) -> TokenMintRecord:
    """Log one mint against the room registry (JWT body is never stored)."""
    _ensure_loaded()
    now = time.time()
    state = expiry_state_for(expires_at, now=now)
    rec = TokenMintRecord(
        ts=now,
        token_id=token_id,
        client_session_id=client_session_id,
        agent_id=agent_id,
        room_id=room_id,
        identity=identity,
        reused=reused,
        dispatch_agent=dispatch_agent,
        issued_at=issued_at,
        expires_at=expires_at,
        ttl_seconds=ttl_seconds,
        expiry_state=state,
    )
    append_mint_record(rec)
    _touch_room(
        room_id=room_id,
        client_session_id=client_session_id,
        agent_id=agent_id,
        token_id=token_id,
        expires_at=expires_at,
        now=now,
    )
    if session is not None:
        session.mint_count = int(session.mint_count or 0) + 1
        session.last_mint_at = now
        session.last_token_id = token_id
        session.last_token_expires_at = expires_at
        upsert_session(session)
    else:
        persist_sessions()
    logger.info(
        "mint logged token_id=%s room=%s expiry_state=%s expires_at=%.0f",
        token_id,
        room_id,
        state,
        expires_at,
    )
    return rec


def record_mint_from_payload(
    payload: Any,
    *,
    client_session_id: str,
    reused: bool,
    dispatch_agent: bool,
    session: VoiceSession | None = None,
) -> TokenMintRecord:
    """Extract expiry fields from ``TokenResponse`` and append to the ledger."""
    issued = float(getattr(payload, "issued_at", None) or time.time())
    expires = float(getattr(payload, "expires_at", None) or (issued + 7200))
    ttl = int(getattr(payload, "ttl_seconds", None) or max(60, int(expires - issued)))
    tid = str(getattr(payload, "token_id", None) or uuid.uuid4().hex[:16])
    return record_token_mint(
        client_session_id=client_session_id,
        agent_id=str(getattr(payload, "agent_id", "") or ""),
        room_id=str(getattr(payload, "room", "") or ""),
        identity=str(getattr(payload, "identity", "") or ""),
        reused=reused,
        dispatch_agent=dispatch_agent,
        token_id=tid,
        issued_at=issued,
        expires_at=expires,
        ttl_seconds=ttl,
        session=session,
    )


def room_id_for(client_session_id: str, agent_id: str) -> str:
    """Stable room name for a (client, agent) pair — never random per mint."""
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
    return True


async def hard_end_session(session: VoiceSession) -> None:
    drop_session(session.client_session_id, session.agent_id)
    await delete_livekit_room(session.room_id)


async def sweep_idle_sessions(*, now: float | None = None) -> list[str]:
    """Hard-end sessions idle past the timeout with no human in the room."""
    _ensure_loaded()
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
            persist_sessions()
            continue
        await hard_end_session(sess)
        ended.append(sess.room_id)
    return ended


def _record_mint(
    sess: VoiceSession,
    *,
    payload: Any,
    reused: bool,
    dispatch_agent: bool,
) -> None:
    record_mint_from_payload(
        payload,
        client_session_id=sess.client_session_id,
        reused=reused,
        dispatch_agent=dispatch_agent,
        session=sess,
    )


async def connect_voice_session(
    *,
    client_session_id: str,
    agent_id: str,
    mint_token: Callable[..., Any],
    greeting_context: str = "web_session",
    identity: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """Remint a JWT for the stable room for this (client, agent).

    * New JWT every Connect (tokens expire) — **same room_id** every time.
    * Each mint is logged with issued_at / expires_at / expiry_state.
    * If agent still in room → reused=True, no RoomAgentDispatch.
    * If agent gone → same room, dispatch again (cold agent, warm room mapping).
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
    # Always the same deterministic room for this pair (registry or formula).
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
        sess.room_id = room
        sess.agent_participant_id = agent_pid
        sess.agent_state = "running"
        sess.last_human_at = time.time()
        payload = mint_token(
            room=room,
            identity=human_id,
            name=display,
            agent_id=aid,
            greeting_context=greeting_context,
            dispatch_agent=False,
            client_session_id=csid,
        )
        _record_mint(sess, payload=payload, reused=True, dispatch_agent=False)
        logger.info(
            "token remint reused room=%s session=%s mints=%d expiry=%s",
            room,
            csid[:12],
            sess.mint_count,
            getattr(payload, "expiry_state", "?"),
        )
        return {
            "payload": payload,
            "reused": True,
            "agent_state": "running",
            "agent_participant_id": agent_pid,
        }

    # Agent not in room — keep stable room id, dispatch agent again.
    sess = existing or VoiceSession(
        client_session_id=csid,
        agent_id=aid,
        room_id=room,
        agent_participant_id=agent_pid,
        last_human_at=time.time(),
        agent_state="starting",
    )
    sess.room_id = room
    sess.agent_participant_id = agent_pid
    sess.agent_state = "starting"
    sess.last_human_at = time.time()
    payload = mint_token(
        room=room,
        identity=human_id,
        name=display,
        agent_id=aid,
        greeting_context=greeting_context,
        dispatch_agent=True,
        client_session_id=csid,
    )
    _record_mint(sess, payload=payload, reused=False, dispatch_agent=True)
    logger.info(
        "token remint cold room=%s session=%s mints=%d expiry=%s",
        room,
        csid[:12],
        sess.mint_count,
        getattr(payload, "expiry_state", "?"),
    )
    return {
        "payload": payload,
        "reused": False,
        "agent_state": "starting",
        "agent_participant_id": agent_pid,
    }
