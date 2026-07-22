"""Companion catalog for the optional Streamlit UI (app/streamlit).

Sources (in order):
- ``src/templates/personalities/*.json`` — classic Luna/Sandra-style templates
- repo ``templates/*.json`` — voice agent templates (Lena, Nia, …)
- ``app/agent/personas/*.json`` — live voice personas
"""

from __future__ import annotations

import concurrent
import itertools
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    import scrapetube
except ImportError:  # optional — only needed for YouTube channel indexing
    scrapetube = None  # type: ignore

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore

RESOURCE_FILE = Path.home() / ".gfgpt" / "ui_resources.json"

_UI_DIR = Path(__file__).resolve().parent  # app/streamlit/utils
_REPO_ROOT = _UI_DIR.parents[2]  # utils → streamlit → app → GirlfriendGPT repo root
_PERSONALITIES_DIR = _REPO_ROOT / "src" / "templates" / "personalities"
_TEMPLATES_DIR = _REPO_ROOT / "templates"
_PERSONAS_DIR = _REPO_ROOT / "app" / "agent" / "personas"

# Back-compat alias used by older call sites.
COMPANION_DIR = _PERSONALITIES_DIR


@dataclass
class CompanionCard:
    key: str
    name: str
    description: str
    source: str  # personality | template | persona
    agent_id: str | None
    voice: bool
    profile_image: str
    attrs: dict[str, Any]


def _load_resources():
    if RESOURCE_FILE.exists():
        with open(RESOURCE_FILE, "r") as f:
            return json.load(f)
    return []


def _save_resources(resources):
    RESOURCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESOURCE_FILE, "w") as f:
        json.dump(resources, f, indent=2)


def add_resource(url: str):
    resources = _load_resources()
    if url not in resources:
        resources.append(url)
        _save_resources(resources)
        return "Added"
    return "Already added"


def index_youtube_channel(
    channel_url: str, offset: Optional[int] = 0, count: Optional[int] = 10
):
    if scrapetube is None:
        raise RuntimeError("scrapetube is not installed")
    if st is None:
        raise RuntimeError("streamlit is not installed")
    videos = scrapetube.get_channel(channel_url=channel_url)

    future_to_url = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        for video in itertools.islice(videos, offset, offset + count + 1):
            video_url = f"https://www.youtube.com/watch?v={video['videoId']}"
            future_to_url[executor.submit(add_resource, video_url)] = video_url

    for ix, future in enumerate(concurrent.futures.as_completed(future_to_url)):
        url = future_to_url[future]
        try:
            data = future.result()
            if "added" in str(data).lower():
                st.write(f"Added {url}")
        except Exception as e:
            st.error(f"Loading {url} generated an exception: {e}")


def index_youtube_video(youtube_url: str):
    if st is None:
        raise RuntimeError("streamlit is not installed")
    data = add_resource(youtube_url)

    if "added" in data.lower():
        st.write(f"Added {youtube_url}")
    else:
        print("error", data)


def get_indexed_resources():
    return _load_resources()


def _join_field(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(x) for x in value)
    return str(value or "")


def _card_from_personality(path: Path) -> CompanionCard | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    name = str(raw.get("name") or path.stem).strip()
    return CompanionCard(
        key=f"personality:{path.stem}",
        name=name,
        description=str(raw.get("description") or raw.get("byline") or ""),
        source="personality",
        agent_id=None,
        voice=False,
        profile_image=str(raw.get("profile_image") or ""),
        attrs={
            "name": name,
            "byline": str(raw.get("byline") or ""),
            "identity": _join_field(raw.get("identity")),
            "behavior": _join_field(raw.get("behavior")),
            "profile_image": str(raw.get("profile_image") or ""),
            "description": str(raw.get("description") or ""),
        },
    )


def _card_from_agent_json(path: Path, source: str) -> CompanionCard | None:
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
    return CompanionCard(
        key=f"{source}:{path.stem}",
        name=name,
        description=str(raw.get("description") or ""),
        source=source,
        agent_id=agent_id,
        voice=voice,
        profile_image=str(raw.get("profile_image") or ""),
        attrs={
            "name": name,
            "byline": str(raw.get("description") or "")[:120],
            "identity": str(raw.get("instructions") or "")[:500],
            "behavior": str(raw.get("greeting") or raw.get("nudge") or ""),
            "profile_image": str(raw.get("profile_image") or ""),
            "description": str(raw.get("description") or ""),
            "agent_id": agent_id,
            "role": role,
        },
    )


def list_companions() -> list[CompanionCard]:
    """All selectable companions for the left sidebar."""
    cards: list[CompanionCard] = []
    seen_names: set[str] = set()

    def _add(card: CompanionCard | None) -> None:
        if card is None:
            return
        # Prefer personas over templates when names collide.
        key = card.name.lower()
        if key in seen_names and card.source != "persona":
            return
        if key in seen_names and card.source == "persona":
            cards[:] = [c for c in cards if c.name.lower() != key]
        seen_names.add(key)
        cards.append(card)

    if _PERSONALITIES_DIR.is_dir():
        for path in sorted(_PERSONALITIES_DIR.glob("*.json")):
            _add(_card_from_personality(path))

    if _TEMPLATES_DIR.is_dir():
        for path in sorted(_TEMPLATES_DIR.glob("*.json")):
            _add(_card_from_agent_json(path, "template"))

    if _PERSONAS_DIR.is_dir():
        for path in sorted(_PERSONAS_DIR.glob("*.json")):
            _add(_card_from_agent_json(path, "persona"))

    return cards


def get_companions() -> list[str]:
    """Legacy: template stems for the optional selectbox."""
    names: list[str] = []
    for card in list_companions():
        names.append(card.name)
    return names


def get_companion_attributes(companion_name: str) -> dict[str, Any]:
    """Legacy: attributes by name (case-insensitive)."""
    needle = companion_name.strip().lower()
    for card in list_companions():
        if card.name.lower() == needle or card.key.lower().endswith(f":{needle}"):
            return dict(card.attrs)
    # Fallback: personalities file stem
    path = _PERSONALITIES_DIR / f"{companion_name}.json"
    if path.is_file():
        card = _card_from_personality(path)
        if card:
            return dict(card.attrs)
    return {}


def get_companion_by_key(key: str) -> CompanionCard | None:
    for card in list_companions():
        if card.key == key:
            return card
    return None
