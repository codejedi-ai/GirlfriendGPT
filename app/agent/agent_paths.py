"""Resolve agent JSON from the self-contained voice package (no ALI).

Canonical layout under ``app/agent/``::

    personas/*.json   # Ella, Nia, …
    tools/*.json      # shared tool defs by id
    data/agents → personas
    data/tools  → tools
    data/templates → repo templates/

Optional env overrides: ``AGENTS_1_DATA``, ``TOOLS_CATALOG_PATH``,
``MODEL_CONFIG_PATH``.
"""

from __future__ import annotations

import os
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parent

REPO_GIRLFRIENDGPT = "GirlfriendGPT"
REPO_AI_GF = "AI-GF"
REPO_URL_GIRLFRIENDGPT = "https://github.com/codejedi-ai/GirlfriendGPT.git"
REPO_URL_AI_GF = "https://github.com/codejedi-ai/AI-GF.git"

# Catalog folder names scanned for personas (in-package first).
CHANNEL_AGENT_DIRS = (
    "personas",
    "GirlfriendGPT-agents",
    "AI-GF-agents",
)
CHANNEL_TEMPLATE_DIRS = {
    REPO_GIRLFRIENDGPT: "GirlfriendGPT-templates",
    REPO_AI_GF: "AI-GF-Templates",
}


def agent_dir() -> Path:
    return _AGENT_DIR


def monorepo_root() -> Path | None:
    for candidate in [_AGENT_DIR, *_AGENT_DIR.parents]:
        if (candidate / "agents" / "GirlfriendGPT").is_dir():
            return candidate
        if (candidate / "agents" / "ali-agents").is_dir():
            return candidate
    return None


def normalize_repo(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    for name in (REPO_GIRLFRIENDGPT, REPO_AI_GF):
        if raw.lower() == name.lower():
            return name
    lower = raw.rstrip("/").lower()
    if "girlfriendgpt" in lower:
        return REPO_GIRLFRIENDGPT
    if "ai-gf" in lower:
        return REPO_AI_GF
    return raw


def resolve_agents_1_data() -> Path:
    """Catalog root: package dir, or ``AGENTS_1_DATA`` override.

    In-package layout uses ``personas/`` and ``tools/`` directly under this root.
    """
    for key in ("AGENTS_1_DATA", "ALI_AGENTS_DATA_PATH"):
        env = (os.getenv(key) or "").strip()
        if env:
            path = Path(env).expanduser().resolve()
            if path.is_dir():
                return path
            raise FileNotFoundError(f"{key} does not exist: {path}")

    # Self-contained: app/agent is the catalog root.
    if (_AGENT_DIR / "personas").is_dir() or (_AGENT_DIR / "data" / "agents").is_dir():
        return _AGENT_DIR.resolve()

    root = monorepo_root()
    if root is not None:
        ali_agents = root / "agents" / "ali-agents"
        if ali_agents.is_dir():
            return ali_agents.resolve()

    local = _AGENT_DIR / "data"
    if (local / "agents").is_dir() or (local / "GirlfriendGPT-agents").is_dir():
        return local.resolve()

    raise FileNotFoundError(
        "Cannot locate agent personas. Expected app/agent/personas/ "
        f"(agent_dir={_AGENT_DIR}). Set AGENTS_1_DATA to override."
    )


def resolve_girlfriendgpt_agents_dir() -> Path:
    base = resolve_agents_1_data()
    for name in ("personas", "GirlfriendGPT-agents", "agents"):
        path = base / name
        if path.is_dir():
            return path.resolve()
    return (base / "personas").resolve()


def resolve_aigf_agents_dir() -> Path:
    return (resolve_agents_1_data() / "AI-GF-agents").resolve()


def resolve_agents_dir() -> Path:
    return resolve_girlfriendgpt_agents_dir()


def iter_agent_catalog_dirs(*, root: Path | None = None) -> list[Path]:
    base = root if root is not None else resolve_agents_1_data()
    dirs: list[Path] = []
    for name in CHANNEL_AGENT_DIRS:
        path = base / name
        if path.is_dir():
            dirs.append(path)
    # Package data/agents symlink or real dir
    legacy = base / "data" / "agents"
    if legacy.is_dir() and any(legacy.glob("*.json")):
        resolved = legacy.resolve()
        if resolved not in {d.resolve() for d in dirs}:
            dirs.append(legacy)
    flat = base / "agents"
    if flat.is_dir() and any(flat.glob("*.json")):
        resolved = flat.resolve()
        if resolved not in {d.resolve() for d in dirs}:
            dirs.append(flat)
    return dirs


def resolve_templates_dir(repo: str | None = None) -> Path:
    root = resolve_agents_1_data()
    want = normalize_repo(repo) if repo else REPO_GIRLFRIENDGPT

    # In-package: data/templates or repo-root templates/
    for candidate in (
        root / "data" / "templates",
        root / "templates",
        resolve_girlfriendgpt_root() / "templates",
    ):
        if candidate.is_dir():
            return candidate.resolve()

    folder = CHANNEL_TEMPLATE_DIRS.get(want)
    if folder:
        path = root / folder
        if path.is_dir():
            return path.resolve()
    legacy = root / "templates"
    if legacy.is_dir():
        return legacy.resolve()
    return root / (folder or CHANNEL_TEMPLATE_DIRS[REPO_GIRLFRIENDGPT])


def resolve_aigf_templates_dir() -> Path:
    return resolve_templates_dir(REPO_AI_GF)


def resolve_tools_1_data() -> Path:
    base = resolve_agents_1_data()
    for candidate in (base / "tools", base / "data" / "tools"):
        if candidate.is_dir():
            return candidate.resolve()
    return (base / "tools").resolve()


def resolve_girlfriendgpt_root() -> Path:
    return _AGENT_DIR.parents[1]


def resolve_model_config_path() -> Path:
    env = (os.getenv("MODEL_CONFIG_PATH") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return (_AGENT_DIR / "config.json").resolve()


def resolve_ali_backend_dir() -> Path:
    """Legacy alias; returns agent dir for standalone package."""
    env = (os.getenv("ALI_BACKEND_DIR") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return _AGENT_DIR


def resolve_ali_root() -> Path:
    return resolve_girlfriendgpt_root()
