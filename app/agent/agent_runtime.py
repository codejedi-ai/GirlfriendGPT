"""Build STT / LLM / TTS / VAD from an agent definition JSON (not config.py)."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_LOCAL_LLM_PROVIDERS = frozenset({"ollama", "lmstudio", "openai_compatible"})

# GirlfriendGPT = local-only channel (Ollama / Speaches / Silero / LM Studio).
# AI-GF = separate third-party cloud channel — do not put those providers here.
_LOCAL_ALLOWED_PROVIDERS = frozenset(
    {"ollama", "lmstudio", "openai_compatible", "speaches", "silero"}
)
_THIRD_PARTY_CLOUD_PROVIDERS = frozenset(
    {
        "openrouter",
        "elevenlabs",
        "anthropic",
        "openai",  # cloud OpenAI API — use openai_compatible + localhost instead
        "azure",
        "gemini",
        "google",
        "groq",
        "deepgram",
        "cartesia",
        "rime",
    }
)

# Keys required on every runnable agent JSON (voice + CLI).
REQUIRED_TOP_LEVEL = (
    "id",
    "name",
    "instructions",
    "packages",
    "repo",
    "participant_id",
)

# Short origin repo names (git remote basename under codejedi-ai).
REPO_GIRLFRIENDGPT = "GirlfriendGPT"
REPO_AI_GF = "AI-GF"
# Legacy full remotes — accepted by normalize_repo for filters/compat.
REPO_URL_GIRLFRIENDGPT = "https://github.com/codejedi-ai/GirlfriendGPT.git"
REPO_URL_AI_GF = "https://github.com/codejedi-ai/AI-GF.git"
KNOWN_REPOS = frozenset({REPO_GIRLFRIENDGPT, REPO_AI_GF})
# Voice LiveKit workers need full speech stack; CLI sub-agents need LLM only.
REQUIRED_VOICE_MODEL_SECTIONS = ("llm", "stt", "tts", "vad")
CLI_ROLES = frozenset({"cli", "sub_agent"})

_PACKAGES_REQUIRED_MSG = (
    "Agent JSON 'packages' must be a non-empty list of dependency names "
    "(declare deps in the persona JSON; do not assume pyproject alone "
    "for that persona)"
)


def normalize_agent_role(role: str | None) -> str:
    raw = (role or "voice").strip().lower().replace("-", "_")
    if raw in {"subagent"}:
        return "sub_agent"
    return raw or "voice"


def is_cli_role(role: str | None) -> bool:
    return normalize_agent_role(role) in CLI_ROLES


def roles_match(stored: str | None, filter_role: str | None) -> bool:
    """True when *filter_role* is empty or matches *stored* (cli ≡ sub_agent)."""
    if filter_role is None or not str(filter_role).strip():
        return True
    stored_n = normalize_agent_role(stored)
    filter_n = normalize_agent_role(filter_role)
    if filter_n in CLI_ROLES:
        return stored_n in CLI_ROLES
    return stored_n == filter_n


def persona_repo(persona: dict[str, Any]) -> str:
    """Resolve owning repo short name from ``repo`` (preferred) or legacy ``repo_url``."""
    from agent_paths import normalize_repo

    return normalize_repo(
        str(persona.get("repo") or persona.get("repo_url") or "").strip()
    )


def _require_repo(persona: dict[str, Any]) -> str:
    """Require non-empty ``repo`` short origin name (e.g. GirlfriendGPT, AI-GF)."""
    # Prefer explicit repo; fall back to legacy repo_url for migration.
    raw = persona.get("repo")
    if raw is None or not str(raw).strip():
        legacy = persona.get("repo_url")
        if legacy is not None and str(legacy).strip():
            name = persona_repo({"repo_url": legacy})
            if name in KNOWN_REPOS:
                return name
        raise ValueError(
            "Agent JSON 'repo' is required (short origin repo name, e.g. "
            f"{REPO_GIRLFRIENDGPT!r} or {REPO_AI_GF!r})"
        )
    name = persona_repo({"repo": raw})
    if name not in KNOWN_REPOS:
        raise ValueError(
            "Agent JSON 'repo' must be a known short origin name "
            f"({REPO_GIRLFRIENDGPT!r} or {REPO_AI_GF!r}); got {raw!r}"
        )
    return name


def is_aigf_repo(persona: dict[str, Any]) -> bool:
    return persona_repo(persona) == REPO_AI_GF


def is_girlfriendgpt_repo(persona: dict[str, Any]) -> bool:
    return persona_repo(persona) == REPO_GIRLFRIENDGPT


def validate_agent_definition(persona: dict[str, Any]) -> None:
    missing = [
        k
        for k in REQUIRED_TOP_LEVEL
        if k not in persona or persona[k] in (None, "")
    ]
    # Allow legacy repo_url alone during migration only if it normalizes.
    if "repo" in missing and persona_repo(persona) in KNOWN_REPOS:
        missing = [k for k in missing if k != "repo"]
    if missing:
        raise ValueError(f"Agent JSON missing required keys: {missing}")
    _require_repo(persona)
    _require_packages_field(persona)
    pid = str(persona.get("participant_id") or "").strip()
    if not pid:
        raise ValueError("Agent JSON 'participant_id' must be a non-empty string")
    if any(ch.isspace() for ch in pid):
        raise ValueError("Agent JSON 'participant_id' must not contain whitespace")
    tools = persona.get("tools")
    if tools is not None:
        if not isinstance(tools, list):
            raise ValueError("Agent JSON 'tools' must be a list of tool id strings")
        for item in tools:
            if isinstance(item, dict):
                raise ValueError(
                    "Agent JSON tools must be id strings only — definitions live in "
                    "ALI/data/tools/<id>.json"
                )

    role = normalize_agent_role(persona.get("role"))
    models = persona.get("models")
    if not isinstance(models, dict):
        raise ValueError("Agent JSON 'models' must be an object")

    # GirlfriendGPT = local providers. AI-GF = third-party — never blend bodies;
    # separation is repo (+ channel folders).
    enforce_local = not is_aigf_repo(persona)

    if is_cli_role(role):
        _validate_llm_section(models)
        if enforce_local:
            _assert_local_providers(models)
        return

    # Voice (default) — full STT/LLM/TTS/VAD contract.
    for section in REQUIRED_VOICE_MODEL_SECTIONS:
        if section not in models or not isinstance(models[section], dict):
            raise ValueError(f"Agent JSON models.{section} is required")
        if not (models[section].get("provider") or "").strip():
            raise ValueError(f"Agent JSON models.{section}.provider is required")
    if "model" not in models["llm"] or not models["llm"]["model"]:
        raise ValueError("Agent JSON models.llm.model is required")
    if "model" not in models["stt"] or not models["stt"]["model"]:
        raise ValueError("Agent JSON models.stt.model is required")
    if enforce_local:
        _assert_local_providers(models)


def _validate_llm_section(models: dict[str, Any]) -> None:
    llm = models.get("llm")
    if not isinstance(llm, dict):
        raise ValueError("Agent JSON models.llm is required")
    if not (llm.get("provider") or "").strip():
        raise ValueError("Agent JSON models.llm.provider is required")
    if "model" not in llm or not llm["model"]:
        raise ValueError("Agent JSON models.llm.model is required")


def _assert_local_providers(models: dict[str, Any]) -> None:
    """GirlfriendGPT personas must stay local; AI-GF owns third-party cloud."""
    for section, cfg in models.items():
        if not isinstance(cfg, dict):
            continue
        provider = (cfg.get("provider") or "").strip().lower()
        if not provider:
            continue
        if provider in _THIRD_PARTY_CLOUD_PROVIDERS:
            raise ValueError(
                f"GirlfriendGPT agent models.{section}.provider={provider!r} "
                "is a third-party cloud provider — use local Ollama/Speaches/"
                "Silero (or openai_compatible + localhost). AI-GF is the "
                "cloud channel."
            )
        if provider not in _LOCAL_ALLOWED_PROVIDERS:
            raise ValueError(
                f"GirlfriendGPT agent models.{section}.provider={provider!r} "
                f"is not a local provider; allowed: {sorted(_LOCAL_ALLOWED_PROVIDERS)}"
            )


def _require_packages_field(persona: dict[str, Any]) -> list[str]:
    """Reject missing / empty / non-list packages; return cleaned names."""
    packages = persona.get("packages")
    if not isinstance(packages, list):
        raise ValueError("Agent JSON 'packages' must be a list of dependency names")
    cleaned = [str(p).strip() for p in packages if str(p).strip()]
    if not cleaned:
        raise ValueError(_PACKAGES_REQUIRED_MSG)
    return cleaned


def should_attach_medication_tools(persona: dict[str, Any]) -> bool:
    """True when persona references report_adherence_intent (or Ella seed)."""
    from agent_persona import ELLA_AGENT_ID

    tools = persona.get("tools") or []
    if isinstance(tools, list) and "report_adherence_intent" in [
        str(t).strip() for t in tools if not isinstance(t, dict)
    ]:
        return True
    if (persona.get("id") or "").strip() == ELLA_AGENT_ID:
        return True
    role = (persona.get("role") or "").strip().lower()
    return role in {"medication", "medication_companion", "med_check", "med-check"}


def declared_packages(persona: dict[str, Any]) -> list[str]:
    raw = persona.get("packages") or []
    if not isinstance(raw, list):
        return []
    return [str(p).strip() for p in raw if str(p).strip()]


def _distribution_installed(name: str) -> bool:
    """True when a distribution matching *name* is importable via metadata."""
    try:
        from importlib import metadata
    except ImportError:  # pragma: no cover
        return False
    needle = (name or "").strip().lower().replace("_", "-")
    if not needle:
        return False
    try:
        metadata.version(needle)
        return True
    except metadata.PackageNotFoundError:
        pass
    # Some envs register with underscores.
    alt = needle.replace("-", "_")
    if alt != needle:
        try:
            metadata.version(alt)
            return True
        except metadata.PackageNotFoundError:
            pass
    return False


def missing_installed_packages(names: list[str]) -> list[str]:
    """Return declared package names that are not installed in this environment."""
    return [n for n in names if not _distribution_installed(n)]


def require_declared_packages(
    persona: dict[str, Any],
    *,
    check_installed: bool = False,
    warn_only_missing: bool = True,
) -> list[str]:
    """Read and enforce the persona ``packages`` array (never silently ignore).

    Always validates a non-empty list. When ``check_installed`` is True, compares
    declared names against the current environment (warn by default; set
    ``warn_only_missing=False`` to raise).
    """
    pkgs = _require_packages_field(persona)
    label = persona.get("name") or persona.get("id") or "?"
    logger.info("Agent %s declares packages: %s", label, ", ".join(pkgs))
    if check_installed:
        missing = missing_installed_packages(pkgs)
        if missing:
            msg = (
                f"Agent {label!r} declares packages not installed in this "
                f"environment: {missing}"
            )
            if warn_only_missing:
                logger.warning(msg)
            else:
                raise ValueError(msg)
    return pkgs


def coalesce_system_messages_first(messages: list[Any]) -> list[Any]:
    """Merge all ``system`` messages into one leading system turn.

    Strict GGUF chat templates (e.g. Qwythos via Ollama) raise
    ``System message must be at the beginning`` when LiveKit injects a
    mid-context system/instructions turn. Coalescing keeps local Ollama
    usable with AgentSession.generate_reply(instructions=...).
    """
    if not messages:
        return messages
    systems: list[Any] = []
    rest: list[Any] = []
    for msg in messages:
        role = ""
        if isinstance(msg, dict):
            role = str(msg.get("role") or "")
        else:
            role = str(getattr(msg, "role", "") or "")
        if role == "system":
            systems.append(msg)
        else:
            rest.append(msg)
    if len(systems) <= 1 and (not systems or not rest or messages[0] is systems[0]):
        # Already a single leading system (or none) — leave unchanged.
        if not systems:
            return messages
        if messages and messages[0] is systems[0] and len(systems) == 1:
            return messages

    def _content(msg: Any) -> str:
        if isinstance(msg, dict):
            content = msg.get("content")
        else:
            content = getattr(msg, "content", None)
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        return str(content)

    merged = {"role": "system", "content": "\n\n".join(_content(m) for m in systems if _content(m))}
    return [merged, *rest]


class _OllamaSystemFirstTransport(httpx.AsyncHTTPTransport):
    """Rewrite chat/completions bodies so system turns are coalesced first."""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        request = _rewrite_chat_completions_system_first(request)
        return await super().handle_async_request(request)


def _rewrite_chat_completions_system_first(request: httpx.Request) -> httpx.Request:
    if "chat/completions" not in str(request.url):
        return request
    raw = request.content
    if not raw:
        return request
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return request
    msgs = data.get("messages")
    if not isinstance(msgs, list):
        return request
    coalesced = coalesce_system_messages_first(msgs)
    if coalesced is msgs:
        return request
    data["messages"] = coalesced
    body = json.dumps(data).encode("utf-8")
    headers = [
        (k, v)
        for k, v in request.headers.multi_items()
        if k.lower() != "content-length"
    ]
    headers.append(("Content-Length", str(len(body))))
    return httpx.Request(
        request.method,
        request.url,
        headers=headers,
        content=body,
        extensions=request.extensions,
    )


def build_llm_from_agent(persona: dict[str, Any]):
    cfg = persona["models"]["llm"]
    provider = (cfg.get("provider") or "").strip()
    model = cfg["model"]
    base_url = cfg.get("base_url") or ""
    if provider in _LOCAL_LLM_PROVIDERS:
        from livekit.plugins.openai import LLM as OpenAICompatLLM
        from openai import AsyncClient

        # Local Ollama/LM Studio: coalesce mid-context system turns so strict
        # GGUF templates (Qwythos) do not 400 on LiveKit instruction injects.
        http_client = httpx.AsyncClient(transport=_OllamaSystemFirstTransport())
        client = AsyncClient(
            api_key=os.getenv("LLM_API_KEY", "not-needed"),
            base_url=base_url or None,
            http_client=http_client,
        )
        return OpenAICompatLLM(model=model, client=client)
    if provider == "openrouter":
        from livekit.plugins.openai import LLM as OpenAICompatLLM

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        return OpenAICompatLLM(
            model=model,
            base_url=base_url or "https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    raise ValueError(f"Unsupported llm provider in agent JSON: {provider!r}")


def build_stt_from_agent(persona: dict[str, Any]):
    cfg = persona["models"]["stt"]
    provider = (cfg.get("provider") or "").strip()
    if provider == "speaches" or provider == "openai_compatible":
        from livekit.plugins import openai

        return openai.STT(
            model=cfg["model"],
            base_url=cfg.get("base_url") or "",
            api_key=os.getenv("SPEECH_API_KEY", "not-needed"),
            detect_language=bool(cfg.get("detect_language", True)),
        )
    if provider == "elevenlabs":
        from livekit.plugins import elevenlabs

        return elevenlabs.STT()
    raise ValueError(f"Unsupported stt provider in agent JSON: {provider!r}")


def build_tts_from_agent(persona: dict[str, Any], *, speed: float | None = None):
    cfg = persona["models"]["tts"]
    provider = (cfg.get("provider") or "").strip()
    tts_speed = float(speed if speed is not None else cfg.get("speed", 1.0))
    if provider == "speaches" or provider == "openai_compatible":
        from livekit.plugins import openai

        routing = cfg.get("routing") or {}
        lang = (cfg.get("default_language") or "en").strip() or "en"
        route = routing.get(lang) or routing.get("en") or cfg
        model = route["model"]
        voice = route["voice"]
        openai.tts.AUDIO_STREAM_MODELS.add(model)
        return openai.TTS(
            model=model,
            voice=voice,
            speed=tts_speed,
            base_url=cfg.get("base_url") or "",
            api_key=os.getenv("SPEECH_API_KEY", "not-needed"),
        )
    if provider == "elevenlabs":
        from livekit.plugins import elevenlabs

        return elevenlabs.TTS(voice_id=cfg["voice_id"])
    raise ValueError(f"Unsupported tts provider in agent JSON: {provider!r}")


def build_vad_from_agent(persona: dict[str, Any]):
    cfg = persona["models"]["vad"]
    provider = (cfg.get("provider") or "").strip()
    if provider == "silero":
        from livekit.plugins import silero

        return silero.VAD.load()
    raise ValueError(f"Unsupported vad provider in agent JSON: {provider!r}")


def log_declared_packages(persona: dict[str, Any]) -> None:
    """Backward-compatible alias — prefer ``require_declared_packages``."""
    require_declared_packages(persona, check_installed=False)
