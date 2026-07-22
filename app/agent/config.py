"""Local GirlfriendGPT voice-worker config (no ALI dependency)."""

from __future__ import annotations

import os
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parent


def agent_name() -> str:
    """LiveKit worker registration name (dispatch target)."""
    return (
        os.getenv("LIVEKIT_AGENT_NAME")
        or os.getenv("AGENT_NAME")
        or "AI-LiveKit-Agent"
    ).strip()


def tools_catalog_path() -> Path:
    env = (os.getenv("TOOLS_CATALOG_PATH") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    try:
        from agent_paths import resolve_tools_1_data

        return resolve_tools_1_data()
    except Exception:  # noqa: BLE001
        for candidate in (_AGENT_DIR / "tools", _AGENT_DIR / "data" / "tools"):
            if candidate.is_dir():
                return candidate.resolve()
        return (_AGENT_DIR / "tools").resolve()
