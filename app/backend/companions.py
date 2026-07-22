"""List companion personas/templates for the Talk UI left bar."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BACKEND_DIR.parents[1]  # GirlfriendGPT
_PERSONAS = _BACKEND_DIR.parent / "agent" / "personas"
_TEMPLATES = _REPO_ROOT / "templates"


def _card_from_agent_json(path: Path, source: str) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    name = str(raw.get("name") or path.stem).strip()
    agent_id = str(raw.get("id") or "").strip() or None
    role = str(raw.get("role") or "").strip().lower()
    models = raw.get("models") or {}
    voice = bool(agent_id) and (role == "voice" or "stt" in models)
    if role == "cli":
        voice = False
    return {
        "key": f"{source}:{path.stem}",
        "name": name,
        "description": str(raw.get("description") or "")[:240],
        "source": source,
        "agent_id": agent_id,
        "participant_id": str(raw.get("participant_id") or "").strip() or None,
        "voice": voice,
        "role": role or None,
    }


def list_companions() -> list[dict[str, Any]]:
    """Talk left bar: templates/ + app/agent/personas/ (persona wins on name clash)."""
    by_name: dict[str, dict[str, Any]] = {}
    priority = {"template": 1, "persona": 2}

    def add(card: dict[str, Any] | None) -> None:
        if not card:
            return
        key = card["name"].lower()
        existing = by_name.get(key)
        if existing is None or priority.get(card["source"], 0) >= priority.get(
            existing["source"], 0
        ):
            by_name[key] = card

    if _TEMPLATES.is_dir():
        for path in sorted(_TEMPLATES.glob("*.json")):
            add(_card_from_agent_json(path, "template"))
    if _PERSONAS.is_dir():
        for path in sorted(_PERSONAS.glob("*.json")):
            add(_card_from_agent_json(path, "persona"))

    return sorted(by_name.values(), key=lambda c: (not c["voice"], c["name"].lower()))
