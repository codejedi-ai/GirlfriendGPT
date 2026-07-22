"""Load tool definitions from the shared JSON catalog.

Canonical directory (ALI-owned)::

    ALI/data/tools/<tool_id>.json

``shared/tools`` is a symlink to that path. Also reachable via package
symlink ``GirlfriendGPT/app/agent/data/tools``, ``TOOLS_CATALOG_PATH``,
or ALI ``tools_catalog_path``.

Agent persona JSON only references tools by id::

    "tools": ["report_adherence_intent", "empathy"]
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_AGENT_DIR = Path(__file__).resolve().parent


def resolve_tools_catalog_dir() -> Path:
    env = (os.getenv("TOOLS_CATALOG_PATH") or "").strip()
    if env:
        return Path(env).expanduser().resolve()

    try:
        import config

        fn = getattr(config, "tools_catalog_path", None)
        if callable(fn):
            path = fn()
            if path is not None:
                return Path(path).resolve()
    except Exception:  # noqa: BLE001
        pass

    linked = _AGENT_DIR / "data" / "tools"
    if linked.exists():
        return linked.resolve()

    try:
        from agent_paths import resolve_tools_1_data

        return resolve_tools_1_data()
    except Exception:  # noqa: BLE001
        pass

    root = None
    for candidate in [_AGENT_DIR, *_AGENT_DIR.parents]:
        if (candidate / "ALI").is_dir() and (candidate / "agents").is_dir():
            root = candidate
            break
    if root is not None:
        for candidate in (
            root / "ALI" / "data" / "tools",
            root / "shared" / "tools",
        ):
            if candidate.is_dir():
                return candidate.resolve()

    raise FileNotFoundError(
        "Cannot locate tools catalog. Set TOOLS_CATALOG_PATH to "
        "ALI/data/tools (agent_dir="
        f"{_AGENT_DIR})"
    )


def list_tool_ids(*, catalog_dir: Path | None = None) -> list[str]:
    root = catalog_dir or resolve_tools_catalog_dir()
    ids: list[str] = []
    for path in sorted(root.glob("*.json")):
        if path.name.upper().startswith("README"):
            continue
        raw = _read_json(path)
        if not raw:
            continue
        tid = str(raw.get("id") or raw.get("name") or path.stem).strip()
        if tid:
            ids.append(tid)
    return ids


def load_tool_definition(
    tool_id: str,
    *,
    catalog_dir: Path | None = None,
) -> dict[str, Any]:
    tid = (tool_id or "").strip()
    if not tid:
        raise KeyError("tool_id is required")
    root = catalog_dir or resolve_tools_catalog_dir()
    path = root / f"{tid}.json"
    if not path.exists():
        for candidate in root.glob("*.json"):
            if candidate.name.upper().startswith("README"):
                continue
            raw = _read_json(candidate)
            if not raw:
                continue
            if str(raw.get("id") or raw.get("name") or "").strip() == tid:
                return raw
        raise KeyError(f"No tool definition for id={tid!r} in {root}")
    raw = _read_json(path)
    if not raw:
        raise KeyError(f"Invalid tool JSON: {path}")
    raw.setdefault("id", tid)
    raw.setdefault("name", tid)
    return raw


def load_tools_for_agent(
    persona: dict[str, Any],
    *,
    catalog_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Resolve persona ``tools`` id list to full catalog definitions."""
    refs = persona.get("tools")
    if refs is None:
        return []
    if not isinstance(refs, list):
        raise ValueError("Agent JSON 'tools' must be a list of tool ids")
    out: list[dict[str, Any]] = []
    for item in refs:
        if isinstance(item, dict):
            raise ValueError(
                "Agent JSON must reference tools by id string, not inline objects. "
                f"Got: {item!r}"
            )
        tid = str(item).strip()
        if not tid:
            continue
        out.append(load_tool_definition(tid, catalog_dir=catalog_dir))
    return out


def tool_ids_from_persona(persona: dict[str, Any]) -> list[str]:
    refs = persona.get("tools") or []
    if not isinstance(refs, list):
        return []
    return [str(x).strip() for x in refs if str(x).strip() and not isinstance(x, dict)]


def to_openai_function(tool: dict[str, Any]) -> dict[str, Any]:
    """OpenAI-compatible function tool envelope (CLI / gateway)."""
    name = str(tool.get("name") or tool.get("id") or "").strip()
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": str(tool.get("description") or ""),
            "parameters": tool.get("parameters")
            if isinstance(tool.get("parameters"), dict)
            else {"type": "object", "properties": {}},
        },
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read tool %s: %s", path, exc)
        return None
    return raw if isinstance(raw, dict) else None
