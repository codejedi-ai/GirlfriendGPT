"""Shim: LiveKit token API lives in ``app/backend``.

Prefer::

    cd app/backend && uv run python main.py

This module re-exports the backend FastAPI app for compatibility with older
``talk-gateway`` docs / commands.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from main import app, main  # noqa: E402

# Compat aliases used by older agent tests
from livekit_token import (  # noqa: E402
    ELLA_AGENT_ID,
    build_token_payload as build_connect_payload,
)

__all__ = ["ELLA_AGENT_ID", "app", "build_connect_payload", "main"]


if __name__ == "__main__":
    main()
