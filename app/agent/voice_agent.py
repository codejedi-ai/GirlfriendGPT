"""
LiveKit Voice Agent Worker — GirlfriendGPT standalone channel.

Persona, models, routing, and packages come from
``app/agent/data/agents/*.json`` (dispatch metadata may carry ``agent_id``).
Worker registration name: ``LIVEKIT_AGENT_NAME`` / ``config.agent_name()``.

Run (from this directory)::

    LIVEKIT_URL=ws://172.16.44.142:7880 \\
    LIVEKIT_API_KEY=devkey \\
    LIVEKIT_API_SECRET=secret \\
    uv run python voice_agent.py dev
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from agent_paths import (
    agent_dir as _agent_dir_fn,
    resolve_girlfriendgpt_root,
    resolve_model_config_path,
)

_AGENT_DIR = _agent_dir_fn()
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

os.environ.setdefault("MODEL_CONFIG_PATH", str(resolve_model_config_path()))

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AgentStateChangedEvent,
    JobContext,
    MetricsCollectedEvent,
    RunContext,
    UserStateChangedEvent,
    WorkerOptions,
    cli,
    function_tool,
    metrics,
)
from livekit.agents.voice.room_io import RoomInputOptions, RoomOutputOptions

import config
from agent_persona import ELLA_AGENT_ID, load_persona
from agent_runtime import (
    build_llm_from_agent,
    build_stt_from_agent,
    build_tts_from_agent,
    build_vad_from_agent,
    require_declared_packages,
    should_attach_medication_tools,
    validate_agent_definition,
)
from tool_catalog import load_tool_definition

_GFGPT_ROOT = resolve_girlfriendgpt_root()
load_dotenv(_AGENT_DIR / ".env")
load_dotenv(_GFGPT_ROOT / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

_LATENCY_BUDGET_MS = 400.0
_BACKEND_API = (os.getenv("GIRLFRIENDGPT_API_URL") or os.getenv("ALI_BACKEND_URL") or "").rstrip("/")
_JOIN_TIMEOUT_SECONDS = 600.0
_MIC_TIMEOUT_SECONDS = 60.0
_SILENCE_NUDGE_SECONDS = 20.0
_MAX_SILENCE_NUDGES = 2
# Local Speaches playback often lacks pause support, so false barge-ins (speaker
# echo into the mic) permanently cut TTS mid-sentence. Require longer / wordy
# interruptions than LiveKit defaults (0.5s / 0 words).
_AEC_WARMUP_SECONDS = 5.0
_latency_buckets: dict[str, dict[str, float]] = {}


def turn_handling_for_local_stack() -> dict[str, Any]:
    """Turn / interruption options tuned for local speaker+mic (no hardware AEC)."""
    return {
        "interruption": {
            "enabled": True,
            "min_duration": 1.5,
            "min_words": 2,
            "resume_false_interruption": True,
            "false_interruption_timeout": 1.5,
        },
    }


def _parse_job_metadata(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        logger.warning("Job metadata is not JSON: %r", text[:200])
        return {}


def _job_metadata(ctx: JobContext) -> dict[str, Any]:
    return _parse_job_metadata(getattr(getattr(ctx, "job", None), "metadata", None))


def _resolve_agent_id_from_meta(meta: dict[str, Any]) -> str:
    """Map job metadata → persona id. Worker name alone → Ella/Lena default."""
    from agent_persona import get_agent_definition

    worker_name = config.agent_name().strip().lower()

    candidates: list[str] = []
    for key in ("agent_id", "id", "persona_id"):
        val = meta.get(key)
        if val is not None and str(val).strip():
            candidates.append(str(val).strip())
    for key in ("agent_name", "name", "livekit_agent_name"):
        val = meta.get(key)
        if val is not None and str(val).strip():
            candidates.append(str(val).strip())
    env_aid = (os.getenv("ALI_AGENT_ID") or os.getenv("GIRLFRIENDGPT_AGENT_ID") or "").strip()
    if env_aid:
        candidates.append(env_aid)

    for raw in candidates:
        token = raw.strip()
        if not token:
            continue
        if token.lower() == worker_name or token.lower() == "ai-livekit-agent":
            continue
        found = get_agent_definition(token)
        if found and found.get("id"):
            return str(found["id"])
        if token.count("-") >= 4:
            return token

    logger.warning(
        "No persona id in job metadata %s — loading Ella %s",
        {k: meta.get(k) for k in ("agent_id", "agent_name", "name") if meta.get(k)},
        ELLA_AGENT_ID,
    )
    return ELLA_AGENT_ID


def _resolve_agent_id(ctx: JobContext) -> str:
    return _resolve_agent_id_from_meta(_job_metadata(ctx))


async def _on_job_request(req: Any) -> None:
    """Accept with permanent persona ``participant_id`` as LiveKit identity."""
    accept = getattr(req, "accept", None)
    job = getattr(req, "job", None)
    if accept is None or job is None:
        return
    meta = _parse_job_metadata(getattr(job, "metadata", None))
    agent_id = _resolve_agent_id_from_meta(meta)
    persona = load_persona(agent_id)
    identity = str(persona.get("participant_id") or "").strip()
    display = str(persona.get("name") or "").strip() or "Agent"
    if not identity:
        from agent_persona import make_participant_id

        identity = make_participant_id(display, agent_id)
    logger.info(
        "Accepting job room=%s identity=%s agent_id=%s name=%s",
        getattr(getattr(req, "room", None), "name", None),
        identity,
        agent_id,
        display,
    )
    await accept(identity=identity, name=display, metadata=json.dumps(meta))

def _backend_base() -> str:
    """Local GirlfriendGPT API (token + agent reach WebSocket fan-out)."""
    return _BACKEND_API or "http://127.0.0.1:8080"


def ring_browser_for_voice(
    *,
    agent_id: str,
    agent_name: str,
    message: str = "wants to talk with you",
    client_session_id: str | None = None,
    auto_answer: bool = True,
) -> dict[str, Any]:
    """POST /api/agent/reach → browser WS opens talk + LiveKit (voice_call).

    Use when the companion should initiate a voice conversation while the user
    is on the local UI (not already in the LiveKit room).
    """
    payload = {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "message": message or "is checking up on you",
        "mode": "voice_call",
        "auto_answer": auto_answer,
        "client_session_id": client_session_id,
        "greeting_context": "reminder_call",
        "purpose": "checkup",
    }
    req = urllib.request.Request(
        f"{_backend_base()}/api/agent/reach",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        logger.info(
            "ring_browser agent=%s delivered=%s",
            agent_id,
            body.get("delivered"),
        )
        return body
    except Exception as exc:  # noqa: BLE001
        logger.warning("ring_browser failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def _fetch_caller_memory(client_session_id: str) -> dict[str, Any]:
    """GET durable memory (name + written notes) for this browser session."""
    csid = (client_session_id or "").strip()
    if not csid:
        return {}
    req = urllib.request.Request(
        f"{_backend_base()}/api/caller-memory/{urllib.parse.quote(csid, safe='')}",
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        mem = body.get("memory") if isinstance(body, dict) else None
        return mem if isinstance(mem, dict) else {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("caller memory fetch failed: %s", exc)
        return {}


def _remember_caller_note(client_session_id: str, note: str) -> dict[str, Any]:
    """Append a written-down fact about the caller (survives cold reconnects)."""
    csid = (client_session_id or "").strip()
    text = (note or "").strip()
    if not csid or not text:
        return {"ok": False, "error": "missing session or note"}
    payload = {"append_note": text}
    req = urllib.request.Request(
        f"{_backend_base()}/api/caller-memory/{urllib.parse.quote(csid, safe='')}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("caller memory write failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def _format_caller_memory_block(mem: dict[str, Any], *, caller_name_hint: str = "") -> str:
    name = str(mem.get("display_name") or caller_name_hint or "").strip()
    summary = str(mem.get("summary") or "").strip()
    notes = mem.get("notes") or []
    if not isinstance(notes, list):
        notes = []
    lines = ["## Who you are talking to (persistent memory — do not forget)"]
    if name:
        lines.append(f"- Their name is {name}. Use it naturally.")
    else:
        lines.append("- Their name is not known yet; ask once warmly if needed.")
    if summary:
        lines.append(f"- Standing summary: {summary}")
    if notes:
        lines.append("- Things you have written down about them:")
        for note in [str(n).strip() for n in notes if str(n).strip()][-12:]:
            lines.append(f"  - {note}")
    lines.append(
        "Treat this block as true for this call. "
        "If they share something important, call remember_about_user to write it down."
    )
    return "\n".join(lines)


def _post_intent(transcript: str, medication_id: str = "") -> dict:
    if not _BACKEND_API:
        logger.warning("No adherence API configured — skipping intent classify")
        return {"ok": False, "skipped": True, "reason": "no_backend_api"}
    payload = {
        "transcript": transcript,
        "medication_id": medication_id or None,
        "use_llm": True,
    }
    req = urllib.request.Request(
        f"{_BACKEND_API}/api/intent/classify",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _load_adherence_description() -> str:
    try:
        desc = str(load_tool_definition("report_adherence_intent").get("description") or "").strip()
        if desc:
            return desc
    except Exception as exc:  # noqa: BLE001
        logger.warning("shared tools catalog missing report_adherence_intent: %s", exc)
    return (
        "Classify the user's medication reply (Taken/Refused/Delayed/"
        "Confused/Distress) and update caregiver alerts. Call this after "
        "every medication-related user answer."
    )


_REPORT_ADHERENCE_DESCRIPTION = _load_adherence_description()


class MedicationCheckAgent(Agent):
    """Medication-check companion; tool *schema* is shared/tools JSON (by id)."""

    def __init__(self, instructions: str, *, client_session_id: str = "") -> None:
        super().__init__(instructions=instructions)
        self._client_session_id = client_session_id

    @function_tool(
        description=(
            "Write down something important about the person you are talking to "
            "(name correction, preference, mood, fact). Survives future calls."
        )
    )
    async def remember_about_user(self, context: RunContext, note: str) -> str:
        result = await asyncio.to_thread(
            _remember_caller_note, self._client_session_id, note
        )
        if result.get("ok") is False and result.get("error"):
            return f"Could not save note: {result.get('error')}"
        return "Saved. You will remember this on future calls."

    @function_tool(description=_REPORT_ADHERENCE_DESCRIPTION)
    async def report_adherence_intent(
        self,
        context: RunContext,
        transcript: str,
        medication_id: str = "",
    ) -> str:
        try:
            data = await asyncio.to_thread(_post_intent, transcript, medication_id)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning("intent classify failed: %s", exc)
            return (
                "Classification unavailable. Respond gently and continue the "
                "medication check-in without mentioning technical problems."
            )

        applied = data.get("applied") or {}
        hint = applied.get("agent_hint") or ""
        state = data.get("state", "")
        logger.info(
            "intent state=%s method=%s action=%s duplicate=%s",
            state,
            data.get("method"),
            applied.get("action"),
            applied.get("duplicate"),
        )
        return (
            f"state={state}; action={applied.get('action')}; "
            f"duplicate={applied.get('duplicate')}; agent_hint={hint}"
        )


class CompanionAgent(Agent):
    """Generic voice companion — no medication tools."""

    def __init__(self, instructions: str, *, client_session_id: str = "") -> None:
        super().__init__(instructions=instructions)
        self._client_session_id = client_session_id

    @function_tool(
        description=(
            "Write down something important about the person you are talking to "
            "(name correction, preference, mood, fact). Survives future calls."
        )
    )
    async def remember_about_user(self, context: RunContext, note: str) -> str:
        result = await asyncio.to_thread(
            _remember_caller_note, self._client_session_id, note
        )
        if result.get("ok") is False and result.get("error"):
            return f"Could not save note: {result.get('error')}"
        return "Saved. You will remember this on future calls."


def _build_agent_instance(
    persona: dict[str, Any],
    instructions: str,
    *,
    client_session_id: str = "",
) -> Agent:
    if should_attach_medication_tools(persona):
        return MedicationCheckAgent(instructions, client_session_id=client_session_id)
    return CompanionAgent(instructions, client_session_id=client_session_id)


def _log_pipeline_latency(ev: MetricsCollectedEvent) -> None:
    metrics.log_metrics(ev.metrics)

    stt_ms = llm_ttft_ms = tts_ttfb_ms = eou_ms = None
    m = ev.metrics
    mtype = getattr(m, "type", None)

    if mtype == "eou_metrics":
        eou_ms = (m.end_of_utterance_delay + m.transcription_delay) * 1000
        logger.info(
            "latency.eou_ms=%.0f (eou_delay=%.0f transcription=%.0f)",
            eou_ms,
            m.end_of_utterance_delay * 1000,
            m.transcription_delay * 1000,
        )
    elif mtype == "llm_metrics":
        llm_ttft_ms = m.ttft * 1000
        logger.info("latency.llm_ttft_ms=%.0f duration_ms=%.0f", llm_ttft_ms, m.duration * 1000)
    elif mtype == "tts_metrics":
        tts_ttfb_ms = m.ttfb * 1000
        logger.info("latency.tts_ttfb_ms=%.0f audio_ms=%.0f", tts_ttfb_ms, m.audio_duration * 1000)
    elif mtype == "stt_metrics":
        stt_ms = m.duration * 1000
        logger.info("latency.stt_ms=%.0f audio_ms=%.0f", stt_ms, m.audio_duration * 1000)

    speech_id = getattr(m, "speech_id", None) or "_"
    bucket = _latency_buckets.setdefault(speech_id, {})
    if eou_ms is not None:
        bucket["eou_ms"] = eou_ms
    if llm_ttft_ms is not None:
        bucket["llm_ttft_ms"] = llm_ttft_ms
    if tts_ttfb_ms is not None:
        bucket["tts_ttfb_ms"] = tts_ttfb_ms
    if stt_ms is not None:
        bucket["stt_ms"] = stt_ms

    if {"eou_ms", "llm_ttft_ms", "tts_ttfb_ms"} <= bucket.keys():
        total = bucket["eou_ms"] + bucket["llm_ttft_ms"] + bucket["tts_ttfb_ms"]
        over = total > _LATENCY_BUDGET_MS
        logger.info(
            "latency.e2e_ms=%.0f budget_ms=%.0f over_budget=%s speech_id=%s parts=%s",
            total,
            _LATENCY_BUDGET_MS,
            over,
            speech_id,
            bucket,
        )
        _latency_buckets.pop(speech_id, None)


def _first_human_participant(ctx: JobContext):
    """Prefer a standard (browser) participant over agents/SIP."""
    remotes = list(ctx.room.remote_participants.values())
    for p in remotes:
        kind = getattr(p, "kind", None)
        # PARTICIPANT_KIND_STANDARD == 0
        if kind in (None, 0):
            return p
    return None


def _participant_has_mic(participant) -> bool:
    """True when the human has published a microphone / audio track."""
    pubs = getattr(participant, "track_publications", None) or {}
    values = pubs.values() if hasattr(pubs, "values") else pubs
    for pub in values:
        kind = getattr(pub, "kind", None)
        source = getattr(pub, "source", None)
        # KIND_AUDIO == 1, SOURCE_MICROPHONE == 2
        if kind == 1 or source == 2:
            return True
        name = str(getattr(pub, "name", "") or "").lower()
        if "mic" in name or name == "microphone":
            return True
    return False


async def _wait_for_patient(ctx: JobContext):
    """Block until a human participant is in the room; return that participant."""
    existing = _first_human_participant(ctx)
    if existing is not None:
        return existing

    joined: asyncio.Future = asyncio.get_running_loop().create_future()

    def _on_joined(participant) -> None:
        if joined.done():
            return
        kind = getattr(participant, "kind", None)
        if kind not in (None, 0):
            return
        joined.set_result(participant)

    ctx.room.on("participant_connected", _on_joined)
    try:
        return await asyncio.wait_for(joined, timeout=_JOIN_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.info(
            "No participant joined room=%s within %.0fs — giving up",
            ctx.room.name,
            _JOIN_TIMEOUT_SECONDS,
        )
        return None
    finally:
        ctx.room.off("participant_connected", _on_joined)


async def _wait_for_patient_mic(ctx: JobContext, patient) -> bool:
    """Block until the human publishes a mic — do not greet before this."""
    if _participant_has_mic(patient):
        return True

    ready: asyncio.Future = asyncio.get_running_loop().create_future()

    def _pub_is_mic(publication) -> bool:
        kind = getattr(publication, "kind", None)
        source = getattr(publication, "source", None)
        if kind == 1 or source == 2:
            return True
        name = str(getattr(publication, "name", "") or "").lower()
        return "mic" in name or name == "microphone"

    def _on_track_published(publication, participant) -> None:
        if ready.done():
            return
        if getattr(participant, "identity", None) != getattr(patient, "identity", None):
            return
        if _pub_is_mic(publication):
            ready.set_result(True)

    ctx.room.on("track_published", _on_track_published)
    try:
        await asyncio.wait_for(ready, timeout=_MIC_TIMEOUT_SECONDS)
        logger.info(
            "Microphone ready identity=%s room=%s",
            getattr(patient, "identity", None),
            ctx.room.name,
        )
        return True
    except asyncio.TimeoutError:
        logger.info(
            "No microphone from identity=%s within %.0fs — giving up greet wait",
            getattr(patient, "identity", None),
            _MIC_TIMEOUT_SECONDS,
        )
        return False
    finally:
        ctx.room.off("track_published", _on_track_published)


class SilenceWatchdog:
    """Nudge if the patient goes quiet after the agent finishes speaking."""

    def __init__(self, session: AgentSession, nudge_instructions: str) -> None:
        self._session = session
        self._nudge_instructions = nudge_instructions
        self._task: asyncio.Task[None] | None = None
        self._nudge_count = 0

    def _cancel(self) -> None:
        if self._task is not None and not self._task.done():
            self._task.cancel()
        self._task = None

    def _schedule(self) -> None:
        self._cancel()
        self._task = asyncio.create_task(self._wait_then_nudge())

    async def _wait_then_nudge(self) -> None:
        try:
            await asyncio.sleep(_SILENCE_NUDGE_SECONDS)
        except asyncio.CancelledError:
            return
        if self._nudge_count >= _MAX_SILENCE_NUDGES:
            return
        self._nudge_count += 1
        logger.info(
            "No response from patient for %.0fs — nudging (%d/%d)",
            _SILENCE_NUDGE_SECONDS,
            self._nudge_count,
            _MAX_SILENCE_NUDGES,
        )
        self._session.generate_reply(
            user_input=f"(Silence nudge for the agent) {self._nudge_instructions}"
        )

    def on_agent_state_changed(self, ev: AgentStateChangedEvent) -> None:
        if ev.new_state == "listening":
            self._schedule()
        else:
            self._cancel()

    def on_user_state_changed(self, ev: UserStateChangedEvent) -> None:
        if ev.new_state == "speaking":
            self._nudge_count = 0
            self._cancel()


def _select_greeting(persona: dict[str, Any], context: str) -> str:
    session_cfg = persona.get("session") or {}
    templates = session_cfg.get("greeting_templates") or {}
    choices = templates.get(context) or []
    if choices:
        return random.choice(choices)
    return str(persona.get("greeting") or "")


async def entrypoint(ctx: JobContext) -> None:
    started = time.perf_counter()
    agent_id = _resolve_agent_id(ctx)
    persona = load_persona(agent_id)
    validate_agent_definition(persona)
    # packages are part of the agent JSON contract — read + optional env check
    require_declared_packages(persona, check_installed=True)

    display = persona.get("name") or agent_id
    logger.info(
        "Voice agent joining room=%s agent_id=%s name=%s llm=%s/%s",
        ctx.room.name,
        agent_id,
        display,
        (persona.get("models") or {}).get("llm", {}).get("provider"),
        (persona.get("models") or {}).get("llm", {}).get("model"),
    )

    await ctx.connect()

    patient = await _wait_for_patient(ctx)
    if patient is None:
        return
    logger.info(
        "Linked to participant identity=%s kind=%s room=%s",
        patient.identity,
        getattr(patient, "kind", None),
        ctx.room.name,
    )

    # Do not start / greet until the browser mic is published.
    if not await _wait_for_patient_mic(ctx, patient):
        return

    meta = _job_metadata(ctx)
    client_session_id = str(meta.get("client_session_id") or "").strip()
    caller_hint = str(meta.get("caller_name") or getattr(patient, "name", "") or "").strip()
    if caller_hint.lower() in {"you", "user"}:
        caller_hint = ""

    mem = await asyncio.to_thread(_fetch_caller_memory, client_session_id) if client_session_id else {}
    if caller_hint and not str(mem.get("display_name") or "").strip() and client_session_id:
        try:
            payload = {"display_name": caller_hint}
            req = urllib.request.Request(
                f"{_backend_base()}/api/caller-memory/{urllib.parse.quote(client_session_id, safe='')}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="PUT",
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            mem = body.get("memory") if isinstance(body, dict) else mem
            if not isinstance(mem, dict):
                mem = {}
        except Exception as exc:  # noqa: BLE001
            logger.warning("seed caller name failed: %s", exc)

    memory_block = _format_caller_memory_block(mem or {}, caller_name_hint=caller_hint)
    base_instructions = str(persona.get("instructions") or "")
    instructions = f"{base_instructions.rstrip()}\n\n{memory_block}\n"
    logger.info(
        "Caller memory session=%s name=%s notes=%d",
        client_session_id[:12] if client_session_id else "-",
        (mem or {}).get("display_name") or caller_hint or "?",
        len((mem or {}).get("notes") or []),
    )

    session = AgentSession(
        vad=build_vad_from_agent(persona),
        stt=build_stt_from_agent(persona),
        llm=build_llm_from_agent(persona),
        tts=build_tts_from_agent(persona),
        turn_handling=turn_handling_for_local_stack(),
        aec_warmup_duration=_AEC_WARMUP_SECONDS,
    )

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent) -> None:
        _log_pipeline_latency(ev)

    nudge = str(persona.get("nudge") or "")
    watchdog = SilenceWatchdog(session, nudge)
    session.on("agent_state_changed", watchdog.on_agent_state_changed)
    session.on("user_state_changed", watchdog.on_user_state_changed)

    # Bind audio to the human before greeting. close_on_disconnect=False so brief
    # browser ICE reconnects do not kill the session (that looked like "deaf").
    # Short-term memory: soft reconnect reuses this AgentSession (no new entrypoint).
    # Long-term memory: instructions above + remember_about_user writes to backend.
    await session.start(
        room=ctx.room,
        agent=_build_agent_instance(
            persona, instructions, client_session_id=client_session_id
        ),
        room_input_options=RoomInputOptions(
            audio_enabled=True,
            text_enabled=True,
            participant_identity=patient.identity,
            close_on_disconnect=False,
        ),
        room_output_options=RoomOutputOptions(
            transcription_enabled=True,
            sync_transcription=True,
            audio_enabled=True,
        ),
    )

    session_cfg = persona.get("session") or {}
    should_greet = bool(session_cfg.get("greet_on_start", True))
    meta_ctx = str(meta.get("greeting_context") or os.getenv("GREETING_CONTEXT") or "").strip()
    if meta_ctx:
        greeting_context = meta_ctx
        if greeting_context == "web_session":
            user_input = "(The user has just connected for a voice conversation.)"
        elif greeting_context == "reminder_call":
            user_input = (
                "(The companion is checking up on the user. Greet warmly, "
                "ask how they are feeling, and keep them company.)"
            )
        else:
            user_input = "(The user has just connected for a voice conversation.)"
    elif should_attach_medication_tools(persona):
        greeting_context = "reminder_call"
        user_input = "(The user has just connected for their scheduled medication check-in.)"
    else:
        greeting_context = "web_session"
        user_input = "(The user has just connected for a voice conversation.)"

    if should_greet:
        greeting_text = (_select_greeting(persona, greeting_context) or "").strip()
        # Speak the template directly — do not LLM-generate the greeting.
        # Local Qwythos often emits "# Response Selection" CoT (and can double-speak)
        # when asked to "greet now" via generate_reply.
        if greeting_text:
            # Greeting must finish — echo often falsely interrupts within 1–2s.
            await session.say(greeting_text, allow_interruptions=False)
        else:
            await session.generate_reply(user_input=user_input)
    logger.info(
        "Agent ready room=%s agent=%s setup_ms=%.0f greet=%s context=%s",
        ctx.room.name,
        display,
        (time.perf_counter() - started) * 1000,
        should_greet,
        greeting_context,
    )


if __name__ == "__main__":
    # Worker registration name (LiveKit dispatch target) — not the human agent name.
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=_on_job_request,
            agent_name=config.agent_name(),
        )
    )
