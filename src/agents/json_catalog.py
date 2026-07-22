"""Load CLI / sub-agent personas from the shared GirlfriendGPT agents folder.

Both voice and CLI agent definitions live under
``GirlfriendGPT/app/agent/data/agents/<uuid>.json``. The CLI channel consumes
the same catalog (filter ``role=cli`` / ``sub_agent``); it does not keep a
duplicate defs tree.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_GFGPT_ROOT = Path(__file__).resolve().parents[2]
_VOICE_AGENT = _GFGPT_ROOT / "app" / "agent"
if str(_VOICE_AGENT) not in sys.path:
    sys.path.insert(0, str(_VOICE_AGENT))

from agent_persona import (  # noqa: E402
    CLI_AGENT_ID,
    CLI_DISPLAY_NAME,
    get_agent_definition,
    list_agent_definitions,
    load_persona,
)
from agent_runtime import (  # noqa: E402
    is_cli_role,
    require_declared_packages,
    validate_agent_definition,
)


def agents_package_dir() -> Path:
    return _VOICE_AGENT


def list_cli_agents(*, base: Path | None = None) -> list[dict[str, Any]]:
    """Catalog rows for CLI / sub-agent personas only."""
    root = base if base is not None else _VOICE_AGENT
    return list_agent_definitions(base=root, role="cli")


def load_cli_agent(agent_id: str | None = None, *, base: Path | None = None) -> dict[str, Any]:
    """Load a full CLI persona JSON; default seed is Nia (``CLI_AGENT_ID``)."""
    root = base if base is not None else _VOICE_AGENT
    aid = (agent_id or "").strip() or CLI_AGENT_ID
    persona = load_persona(aid, base=root)
    if not is_cli_role(persona.get("role")):
        raise ValueError(
            f"Agent {aid!r} role={persona.get('role')!r} is not a CLI/sub_agent persona"
        )
    validate_agent_definition(persona)
    require_declared_packages(persona)
    return persona


def get_cli_agent_definition(ref: str | None = None, *, base: Path | None = None) -> dict[str, Any] | None:
    root = base if base is not None else _VOICE_AGENT
    token = (ref or "").strip() or CLI_AGENT_ID
    view = get_agent_definition(token, base=root)
    if view is None or not is_cli_role(view.get("role")):
        return None
    return view


__all__ = [
    "CLI_AGENT_ID",
    "CLI_DISPLAY_NAME",
    "agents_package_dir",
    "get_cli_agent_definition",
    "list_cli_agents",
    "load_cli_agent",
]
