"""Periodic companion check-ups over the local events WebSocket.

When a browser is connected and the user is not already in a live voice call,
the backend rings them (``mode=voice_call``) so the companion can check up.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from livekit_token import default_agent_id
from local_events import ReachRequest, hub, publish_agent_reach
from voice_sessions import sessions_for_client

logger = logging.getLogger("checkup")


def checkup_enabled() -> bool:
    # Off by default — Streamlit (app/streamlit) owns the chron / random schedule.
    raw = (os.getenv("CHECKUP_ENABLED") or "0").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def checkup_interval_seconds() -> int:
    raw = (os.getenv("CHECKUP_INTERVAL_SECONDS") or "600").strip()
    try:
        return max(60, int(raw))
    except ValueError:
        return 600


def checkup_initial_seconds() -> int:
    """Wait after first WS hello before the first check-up ring."""
    raw = (os.getenv("CHECKUP_INITIAL_SECONDS") or "120").strip()
    try:
        return max(30, int(raw))
    except ValueError:
        return 120


def _companion_for_checkup() -> tuple[str, str]:
    aid = default_agent_id()
    name = (os.getenv("CHECKUP_AGENT_NAME") or "").strip() or "Lena Van Der Meer"
    override = (os.getenv("CHECKUP_AGENT_ID") or "").strip()
    if override:
        aid = override
    return aid, name


def _client_busy_in_voice(client_session_id: str | None) -> bool:
    if not client_session_id:
        return False
    # Soft signal from browser (most reliable while talk pane is open).
    # Also skip if a voice session was touched recently (human connected).
    now = time.time()
    for sess in sessions_for_client(client_session_id):
        if now - sess.last_human_at < 120:
            return True
    return False


async def run_checkup_once(*, now: float | None = None) -> list[dict[str, Any]]:
    """Ring eligible connected browsers. Returns list of reach results."""
    if not checkup_enabled():
        return []
    ts = now if now is not None else time.time()
    interval = checkup_interval_seconds()
    initial = checkup_initial_seconds()
    agent_id, agent_name = _companion_for_checkup()
    results: list[dict[str, Any]] = []

    for client in hub.snapshot_clients():
        sid = client.client_session_id
        if not sid:
            continue
        if client.talk_live:
            continue
        if _client_busy_in_voice(sid):
            continue
        # First ring after initial delay from connect/hello; then every interval.
        anchor = client.last_checkup_at or client.connected_at
        if client.last_checkup_at is None:
            if ts - client.connected_at < initial:
                continue
        elif ts - anchor < interval:
            continue

        result = await publish_agent_reach(
            ReachRequest(
                agent_id=agent_id,
                agent_name=agent_name,
                message="is checking up on you",
                mode="voice_call",
                auto_answer=True,
                client_session_id=sid,
                greeting_context="reminder_call",
                purpose="checkup",
            )
        )
        client.last_checkup_at = ts
        results.append(result)
        logger.info(
            "checkup ring session=%s delivered=%s",
            sid[:12],
            result.get("delivered"),
        )
    return results


async def checkup_loop() -> None:
    """Background task: tick every 30s and ring when due."""
    logger.info(
        "checkup loop started enabled=%s interval=%ss initial=%ss",
        checkup_enabled(),
        checkup_interval_seconds(),
        checkup_initial_seconds(),
    )
    while True:
        try:
            await asyncio.sleep(30)
            if checkup_enabled():
                await run_checkup_once()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("checkup loop tick failed")
