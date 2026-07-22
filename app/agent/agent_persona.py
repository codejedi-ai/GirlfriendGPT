"""Agent definitions for the self-contained GirlfriendGPT voice package.

Canonical catalog (in-package)::

    app/agent/personas/<Name>.json
    app/agent/tools/<id>.json

Filenames are the display name (``Lena Van Der Meer.json``, ``Nia.json``); the ``id`` field
inside the JSON is the stable key. Each persona requires ``repo``
(``GirlfriendGPT`` or ``AI-GF``). ``packages`` is required and non-empty.
Tools are id refs under ``app/agent/tools/``.

``data/agents`` / ``data/tools`` / ``data/templates`` symlink into the
in-package dirs (or repo templates).
"""

from __future__ import annotations

import copy
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any

from agent_paths import (
    REPO_AI_GF,
    REPO_GIRLFRIENDGPT,
    REPO_URL_GIRLFRIENDGPT,
    iter_agent_catalog_dirs,
    normalize_repo,
    resolve_agents_1_data,
    resolve_agents_dir,
    resolve_templates_dir,
)

logger = logging.getLogger(__name__)

AGENT_DIR = Path(__file__).resolve().parent
DATA_DIR = AGENT_DIR / "data"
AGENTS_DATA_DIR = DATA_DIR / "agents"
TEMPLATES_DIR = DATA_DIR / "templates"
DEFAULT_TEMPLATE_PATH = TEMPLATES_DIR / "medication_companion.json"

ELLA_AGENT_ID = "e11a0000-0000-4000-8000-000000000001"
ELLA_DISPLAY_NAME = "Lena Van Der Meer"
CLI_AGENT_ID = "c11a0000-0000-4000-8000-000000000001"
CLI_DISPLAY_NAME = "Nia"
ELIZA_AGENT_ID = "a11a0000-0000-4000-8000-000000000001"
ELIZA_DISPLAY_NAME = "Eliza"


def looks_like_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value).strip())
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def make_livekit_agent_name(display_name: str, agent_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (display_name or "").strip().lower()).strip("-")
    if not slug:
        slug = "agent"
    short = (agent_id or "").replace("-", "")[:8] or uuid.uuid4().hex[:8]
    return f"{slug}-{short}"


def make_participant_id(display_name: str, agent_id: str) -> str:
    """Permanent LiveKit participant identity for this persona (not the job id)."""
    slug = re.sub(r"[^a-z0-9]+", "-", (display_name or "").strip().lower()).strip("-")
    if not slug:
        slug = "agent"
    short = (agent_id or "").replace("-", "")[:8] or uuid.uuid4().hex[:8]
    return f"agent-{slug}-{short}"


def _seed_filename_for_id(agent_id: str) -> str | None:
    """Preferred on-disk name for seeded personas (display name, not uuid)."""
    aid = (agent_id or "").strip()
    if aid == ELLA_AGENT_ID:
        return f"{ELLA_DISPLAY_NAME}.json"
    if aid == CLI_AGENT_ID:
        return f"{CLI_DISPLAY_NAME}.json"
    if aid == ELIZA_AGENT_ID:
        return f"{ELIZA_DISPLAY_NAME}.json"
    return None


def agents_dir(*, base: Path | None = None) -> Path:
    """GirlfriendGPT personas dir (package symlink or 1-data channel folder)."""
    if base is not None:
        return Path(base) / "data" / "agents"
    try:
        return resolve_agents_dir()
    except FileNotFoundError:
        return AGENT_DIR / "data" / "agents"


def _catalog_dirs(*, base: Path | None = None) -> list[Path]:
    """Dirs to scan for personas.

    When *base* is the live GirlfriendGPT package (``AGENT_DIR``), scan both
    channel folders under ``ALI/data`` so AI-GF agents (Eliza) resolve the
    same way they appear in list APIs. When *base* is a catalog root
    (``ALI/data`` or upload/sync override with ``*-agents`` folders), scan
    those channel dirs. Isolated package-style trees still use
    ``base/data/agents`` only.
    """
    if base is not None:
        base_p = Path(base).resolve()
        if base_p == AGENT_DIR.resolve():
            try:
                dirs = iter_agent_catalog_dirs()
                if dirs:
                    return dirs
            except FileNotFoundError:
                pass
        channel = iter_agent_catalog_dirs(root=base_p)
        if channel:
            return channel
        return [base_p / "data" / "agents"]
    try:
        dirs = iter_agent_catalog_dirs()
        if dirs:
            return dirs
    except FileNotFoundError:
        pass
    return [agents_dir()]


def _read_raw(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read persona %s: %s", path, exc)
        return None
    return raw if isinstance(raw, dict) else None


def absolute_prompt_path(agent_id: str, *, base: Path | None = None) -> Path:
    """Resolve persona file by ``id`` field (filename may be name or uuid)."""
    aid = (agent_id or "").strip()
    directories = _catalog_dirs(base=base)
    for directory in directories:
        legacy = directory / f"{aid}.json"
        if legacy.exists():
            return legacy
        if directory.exists():
            for path in sorted(directory.glob("*.json")):
                raw = _read_raw(path)
                if raw and (raw.get("id") or "").strip() == aid:
                    return path
    seed_name = _seed_filename_for_id(aid)
    # Prefer GirlfriendGPT-agents for Ella/Nia; AI-GF-agents for Eliza.
    if aid == ELIZA_AGENT_ID:
        for directory in directories:
            if directory.name == "AI-GF-agents":
                return directory / (seed_name or f"{aid}.json")
    primary = directories[0] if directories else agents_dir(base=base)
    if seed_name:
        return primary / seed_name
    return primary / f"{aid}.json"


def _prompt_path_for(path: Path, *, base: Path | None = None) -> str:
    """Channel-relative path under ``*-agents``; else package ``data/agents/...``."""
    parent = path.parent
    parent_name = parent.name
    if parent_name in ("GirlfriendGPT-agents", "AI-GF-agents"):
        return f"{parent_name}/{path.name}"
    # Legacy flat catalog: ALI/data/agents/<file>.json
    if parent_name == "agents" and parent.parent.name == "1-data":
        return f"agents/{path.name}"
    if base is not None:
        return f"data/agents/{path.name}"
    return f"{parent_name}/{path.name}"


def relative_prompt_path(agent_id: str, *, base: Path | None = None) -> str:
    """Catalog-relative path for API / package layout."""
    path = absolute_prompt_path(agent_id, base=base)
    return _prompt_path_for(path, base=base)


def _replace_name(value: Any, display: str) -> Any:
    if isinstance(value, str):
        return value.replace("{name}", display)
    if isinstance(value, list):
        return [_replace_name(v, display) for v in value]
    if isinstance(value, dict):
        return {k: _replace_name(v, display) for k, v in value.items()}
    return value


def load_template() -> dict[str, Any]:
    path = DEFAULT_TEMPLATE_PATH
    if not path.exists():
        try:
            path = resolve_templates_dir(REPO_GIRLFRIENDGPT) / "medication_companion.json"
        except FileNotFoundError:
            path = DEFAULT_TEMPLATE_PATH
    if not path.exists():
        return {
            "repo": REPO_GIRLFRIENDGPT,
            "packages": ["livekit-agents", "livekit-plugins-openai", "livekit-plugins-silero"],
            "models": {
                "llm": {
                    "provider": "ollama",
                    "model": "required",
                    "base_url": "http://localhost:11434/v1",
                },
                "stt": {
                    "provider": "speaches",
                    "model": "required",
                    "base_url": "http://localhost:8000/v1",
                    "detect_language": True,
                },
                "tts": {
                    "provider": "speaches",
                    "base_url": "http://localhost:8000/v1",
                    "speed": 0.85,
                    "default_language": "en",
                    "routing": {
                        "en": {"model": "required", "voice": "af_heart"},
                    },
                },
                "vad": {"provider": "silero"},
            },
            "session": {"greet_on_start": True, "greeting_templates": {}},
            "instructions": "You are {name}.",
            "greeting": "Greet them warmly.",
            "nudge": "Gently check if they are still there.",
        }
    return json.loads(path.read_text(encoding="utf-8"))


def build_persona_payload(
    *,
    agent_id: str,
    name: str,
    role: str = "voice",
    template: dict[str, Any] | None = None,
    livekit_agent_name: str | None = None,
    repo: str | None = None,
    repo_url: str | None = None,
) -> dict[str, Any]:
    from agent_runtime import validate_agent_definition

    tpl = copy.deepcopy(template or load_template())
    display = (name or "").strip()
    lk = (livekit_agent_name or "").strip() or make_livekit_agent_name(display, agent_id)
    participant_id = (
        str(tpl.get("participant_id") or "").strip()
        or make_participant_id(display, agent_id)
    )
    repo_name = normalize_repo(
        repo or repo_url or tpl.get("repo") or tpl.get("repo_url") or REPO_GIRLFRIENDGPT
    ) or REPO_GIRLFRIENDGPT
    payload: dict[str, Any] = {
        "repo": repo_name,
        "id": agent_id,
        "name": display,
        "role": (role or "voice").strip() or "voice",
        "livekit_agent_name": lk,
        "participant_id": participant_id,
        "tools": list(tpl.get("tools") or []),
        "packages": list(tpl.get("packages") or []),
        "models": copy.deepcopy(tpl.get("models") or {}),
        "session": _replace_name(copy.deepcopy(tpl.get("session") or {}), display),
        "instructions": _replace_name(str(tpl.get("instructions") or ""), display),
        "greeting": _replace_name(str(tpl.get("greeting") or ""), display),
        "nudge": _replace_name(str(tpl.get("nudge") or ""), display),
    }
    desc = (tpl.get("description") or "").strip()
    if desc:
        payload["description"] = _replace_name(desc, display)
    validate_agent_definition(payload)
    return payload


def write_persona(
    *,
    agent_id: str,
    name: str,
    role: str = "voice",
    template: dict[str, Any] | None = None,
    livekit_agent_name: str | None = None,
    repo: str | None = None,
    repo_url: str | None = None,
    base: Path | None = None,
) -> Path:
    path = absolute_prompt_path(agent_id, base=base)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_persona_payload(
        agent_id=agent_id,
        name=name,
        role=role,
        template=template,
        livekit_agent_name=livekit_agent_name,
        repo=repo,
        repo_url=repo_url,
    )
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _catalog_view(
    raw: dict[str, Any],
    *,
    path: Path,
    base: Path | None = None,
) -> dict[str, Any]:
    """Slim fields for API/list; full file remains on disk for the worker."""
    aid = (raw.get("id") or path.stem or "").strip()
    name = (raw.get("name") or "").strip()
    if not aid or not name or not looks_like_uuid(aid):
        return {}
    lk = (raw.get("livekit_agent_name") or "").strip() or make_livekit_agent_name(name, aid)
    participant_id = (
        str(raw.get("participant_id") or "").strip() or make_participant_id(name, aid)
    )
    repo_name = normalize_repo(raw.get("repo") or raw.get("repo_url"))
    view: dict[str, Any] = {
        "id": aid,
        "name": name,
        "role": (raw.get("role") or "voice").strip() or "voice",
        "repo": repo_name,
        "livekit_agent_name": lk,
        "participant_id": participant_id,
        "prompt_path": _prompt_path_for(path, base=base),
        "packages": list(raw.get("packages") or []),
        "models": raw.get("models") if isinstance(raw.get("models"), dict) else {},
    }
    desc = (raw.get("description") or "").strip()
    if desc:
        view["description"] = desc
    return view


def list_agent_definitions(
    *,
    base: Path | None = None,
    role: str | None = None,
    repo: str | None = None,
    repo_url: str | None = None,
) -> list[dict[str, Any]]:
    """Scan channel persona folders under ``ALI/data``.

    Optional *role* filters (``cli`` ≡ ``sub_agent``). Optional *repo* (preferred)
    or legacy *repo_url* filters by owning origin (GirlfriendGPT vs AI-GF).
    """
    from agent_runtime import roles_match

    want_repo = normalize_repo(repo or repo_url) or None
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for directory in _catalog_dirs(base=base):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json")):
            raw = _read_raw(path)
            if not raw:
                continue
            view = _catalog_view(raw, path=path, base=base)
            if not view:
                continue
            if view["id"] in seen:
                continue
            if not roles_match(view.get("role"), role):
                continue
            if want_repo is not None:
                got = normalize_repo(view.get("repo"))
                if got != want_repo:
                    continue
            seen.add(view["id"])
            out.append(view)
    return out


def get_agent_definition(
    ref: str | None,
    *,
    base: Path | None = None,
) -> dict[str, Any] | None:
    token = (ref or "").strip()
    if not token:
        return None
    if looks_like_uuid(token):
        path = absolute_prompt_path(token, base=base)
        raw = _read_raw(path) if path.exists() else None
        if not raw:
            return None
        return _catalog_view(raw, path=path, base=base) or None
    needle = token.lower()
    for persona in list_agent_definitions(base=base):
        if (persona.get("name") or "").strip().lower() == needle:
            return persona
        if (persona.get("livekit_agent_name") or "").strip().lower() == needle:
            return persona
    return None


def load_persona(agent_id: str, *, base: Path | None = None) -> dict[str, Any]:
    """Load full agent JSON (voice or CLI) — models + prompt + packages.

    Accepts UUID id, display name, or ``livekit_agent_name``. The LiveKit
    worker registration name (e.g. ``AI-LiveKit-Agent``) is not a persona —
    callers should resolve that to Ella before calling here.
    """
    from agent_runtime import validate_agent_definition

    aid = (agent_id or "").strip()
    if not aid:
        raise KeyError("agent_id is required to load a persona")

    raw: dict[str, Any] | None = None
    path: Path | None = None

    if looks_like_uuid(aid):
        path = absolute_prompt_path(aid, base=base)
        raw = _read_raw(path) if path.exists() else None

    if raw is None:
        view = get_agent_definition(aid, base=base)
        if view is not None:
            resolved_id = str(view.get("id") or "").strip()
            if resolved_id:
                path = absolute_prompt_path(resolved_id, base=base)
                raw = _read_raw(path) if path.exists() else None
                if raw is None:
                    # Catalog view already has fields; use file-backed merge
                    raw = dict(view)

    if raw is None:
        # Last resort: worker-name / unknown → Ella
        if aid.lower() in {"ai-livekit-agent", "ella"} or not looks_like_uuid(aid):
            path = absolute_prompt_path(ELLA_AGENT_ID, base=base)
            raw = _read_raw(path) if path.exists() else None
            if raw is not None:
                aid = ELLA_AGENT_ID

    if raw is None:
        raise KeyError(f"No agent definition for id={aid!r}")
    if not (raw.get("instructions") or "").strip():
        raise KeyError(f"Agent {aid!r} has empty instructions")
    raw.setdefault("id", aid if looks_like_uuid(aid) else raw.get("id") or aid)
    if path is not None:
        raw.setdefault("prompt_path", _prompt_path_for(path, base=base))
    if not raw.get("repo") and raw.get("repo_url"):
        raw["repo"] = normalize_repo(raw.get("repo_url"))
    if not str(raw.get("participant_id") or "").strip():
        display = str(raw.get("name") or "").strip() or "agent"
        pid_aid = str(raw.get("id") or aid).strip()
        raw["participant_id"] = make_participant_id(display, pid_aid)
    validate_agent_definition(raw)
    return raw


def delete_persona(agent_id: str, *, base: Path | None = None) -> bool:
    path = absolute_prompt_path(agent_id, base=base)
    if not path.exists():
        return False
    path.unlink()
    return True


def ensure_ella_persona_file(*, base: Path | None = None) -> Path:
    """Seed Ella JSON if missing. Prefer the repo seed file over the template."""
    path = absolute_prompt_path(ELLA_AGENT_ID, base=base)
    if path.exists():
        return path
    canonical = absolute_prompt_path(ELLA_AGENT_ID)
    if base is not None and canonical.exists() and Path(base).resolve() != AGENT_DIR.resolve():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical.read_text(encoding="utf-8"), encoding="utf-8")
        return path
    return write_persona(
        agent_id=ELLA_AGENT_ID,
        name=ELLA_DISPLAY_NAME,
        role="voice",
        repo=REPO_GIRLFRIENDGPT,
        livekit_agent_name=make_livekit_agent_name(ELLA_DISPLAY_NAME, ELLA_AGENT_ID),
        base=base,
    )


def ensure_cli_persona_file(*, base: Path | None = None) -> Path:
    """Seed Nia (CLI sub-agent) JSON if missing."""
    path = absolute_prompt_path(CLI_AGENT_ID, base=base)
    if path.exists():
        return path
    canonical = absolute_prompt_path(CLI_AGENT_ID)
    if base is not None and canonical.exists() and Path(base).resolve() != AGENT_DIR.resolve():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical.read_text(encoding="utf-8"), encoding="utf-8")
        return path
    raise FileNotFoundError(
        f"CLI agent seed missing at {canonical}; expected role=cli packages JSON"
    )


def one_data_root() -> Path:
    """Expose ``ALI/data`` for callers / tests."""
    return resolve_agents_1_data()


# Back-compat aliases used by older imports/tests.
REPO_URL_AI_GF = "https://github.com/codejedi-ai/AI-GF.git"
__all__ = [
    "AGENTS_DATA_DIR",
    "CLI_AGENT_ID",
    "CLI_DISPLAY_NAME",
    "ELLA_AGENT_ID",
    "ELLA_DISPLAY_NAME",
    "ELIZA_AGENT_ID",
    "ELIZA_DISPLAY_NAME",
    "REPO_AI_GF",
    "REPO_GIRLFRIENDGPT",
    "REPO_URL_AI_GF",
    "REPO_URL_GIRLFRIENDGPT",
    "absolute_prompt_path",
    "agents_dir",
    "build_persona_payload",
    "delete_persona",
    "ensure_cli_persona_file",
    "ensure_ella_persona_file",
    "get_agent_definition",
    "list_agent_definitions",
    "load_persona",
    "load_template",
    "looks_like_uuid",
    "make_livekit_agent_name",
    "make_participant_id",
    "one_data_root",
    "relative_prompt_path",
    "write_persona",
]
