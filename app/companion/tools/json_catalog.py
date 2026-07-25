"""CLI / gateway bridge: load OpenAI-format tools from the shared JSON catalog.

GirlfriendGPT CLI is an ALI **sub-agent** channel. Tool *definitions* are not
duplicated in Python or persona files — they live in ``shared/tools/<id>.json``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_GFGPT_ROOT = Path(__file__).resolve().parents[2]
_VOICE_AGENT = _GFGPT_ROOT / "app" / "agent"
if str(_VOICE_AGENT) not in sys.path:
    sys.path.insert(0, str(_VOICE_AGENT))

from tool_catalog import (  # noqa: E402
    load_tool_definition,
    load_tools_for_agent,
    resolve_tools_catalog_dir,
    to_openai_function,
)


def shared_catalog_dir() -> Path:
    env = (os.getenv("TOOLS_CATALOG_PATH") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return resolve_tools_catalog_dir()


def openai_tools_for_ids(tool_ids: list[str]) -> list[dict[str, Any]]:
    """Resolve tool id list → OpenAI function envelopes for the CLI/gateway."""
    return [to_openai_function(load_tool_definition(tid)) for tid in tool_ids]


def openai_tools_for_persona(persona: dict[str, Any]) -> list[dict[str, Any]]:
    return [to_openai_function(t) for t in load_tools_for_agent(persona)]
