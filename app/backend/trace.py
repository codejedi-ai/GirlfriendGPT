"""Trace recorder — every tool call records a step.

Steps go to two places: the in-memory session buffer (fast lookup during
the running session) and the store (durable JSONL written at session
finalize). The reflection pipeline reads from the store.

The recorder is also the source of the **intent fingerprint** + **tool
sequence hash** used by the pattern detector to cluster traces.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from .store import Store


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TraceStep:
    """One tool invocation inside a session."""

    session_id: str
    agent: str
    tool: str
    args: dict[str, Any]
    result_summary: str
    duration_ms: float
    llm_tokens: int = 0
    success: bool = True
    error: str | None = None
    recorded_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["recorded_at"] = self.recorded_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TraceStep":
        return cls(
            session_id=d["session_id"],
            agent=d["agent"],
            tool=d["tool"],
            args=d["args"],
            result_summary=d["result_summary"],
            duration_ms=d["duration_ms"],
            llm_tokens=d.get("llm_tokens", 0),
            success=d.get("success", True),
            error=d.get("error"),
            recorded_at=datetime.fromisoformat(d["recorded_at"]),
        )


@dataclass
class TraceSession:
    """All steps + the originating intent for one user request."""

    session_id: str
    intent_text: str
    steps: list[TraceStep] = field(default_factory=list)
    succeeded: bool = True
    started_at: datetime = field(default_factory=_utcnow)
    finished_at: datetime | None = None

    @property
    def tool_sequence(self) -> list[str]:
        return [s.tool for s in self.steps if s.success]

    @property
    def total_llm_tokens(self) -> int:
        return sum(s.llm_tokens for s in self.steps)

    @property
    def total_duration_ms(self) -> float:
        return sum(s.duration_ms for s in self.steps)


# ---------- fingerprinting ----------

_NORMALIZE_RE = re.compile(r"[^a-z0-9 ]+")


def normalize_intent(text: str) -> str:
    """Lowercase, strip URLs/digits/punct, keep keyword shape only.

    URLs and IDs are noise for clustering. We want
    'scrape https://example.com/listing/1' and
    'scrape https://example.com/listing/99' to fingerprint the same.
    """
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\b\d+\b", " n ", text)
    text = _NORMALIZE_RE.sub(" ", text)
    return " ".join(text.split())


def intent_hash(text: str) -> str:
    return hashlib.sha256(normalize_intent(text).encode()).hexdigest()[:16]


def tool_seq_hash(tools: list[str]) -> str:
    return hashlib.sha256(" -> ".join(tools).encode()).hexdigest()[:16]


# ---------- recorder ----------


class TraceRecorder:
    """In-memory recorder with optional ``Store``-backed durable sink.

    Use ``start_session(intent)`` to begin, ``record(...)`` per tool call,
    and ``finalize(session_id, succeeded)`` to write JSONL into the store.
    The returned store key is the JSONL path; pattern detection reads it.
    """

    def __init__(self, store: Store | None = None) -> None:
        self._store = store
        self._sessions: dict[str, TraceSession] = {}

    def start_session(self, intent_text: str, session_id: str) -> TraceSession:
        sess = TraceSession(session_id=session_id, intent_text=intent_text)
        self._sessions[session_id] = sess
        return sess

    def get(self, session_id: str) -> TraceSession:
        return self._sessions[session_id]

    def record(self, step: TraceStep) -> None:
        sess = self._sessions.get(step.session_id)
        if sess is None:
            raise KeyError(
                f"no session {step.session_id}; call start_session first"
            )
        sess.steps.append(step)

    def finalize(self, session_id: str, succeeded: bool = True) -> str | None:
        sess = self._sessions.get(session_id)
        if sess is None:
            return None
        sess.succeeded = succeeded
        sess.finished_at = _utcnow()
        if self._store is None:
            return None
        key = self._jsonl_key(sess)
        lines = [
            json.dumps(
                {
                    "kind": "header",
                    "session_id": sess.session_id,
                    "intent_text": sess.intent_text,
                    "intent_hash": intent_hash(sess.intent_text),
                    "tool_seq_hash": tool_seq_hash(sess.tool_sequence),
                    "succeeded": sess.succeeded,
                    "started_at": sess.started_at.isoformat(),
                    "finished_at": (
                        sess.finished_at.isoformat() if sess.finished_at else None
                    ),
                }
            )
        ]
        for s in sess.steps:
            lines.append(json.dumps({"kind": "step", **s.to_dict()}))
        self._store.put(key, "\n".join(lines) + "\n")
        return key

    @staticmethod
    def _jsonl_key(sess: TraceSession) -> str:
        date = sess.started_at.strftime("%Y-%m-%d")
        return str(PurePosixPath("traces") / date / f"{sess.session_id}.jsonl")


def load_trace_jsonl(blob: bytes | str) -> tuple[dict[str, Any], list[TraceStep]]:
    """Reverse of ``finalize``'s write — parse a JSONL trace file."""
    if isinstance(blob, bytes):
        blob = blob.decode("utf-8")
    header: dict[str, Any] = {}
    steps: list[TraceStep] = []
    for line in blob.splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        kind = rec.pop("kind")
        if kind == "header":
            header = rec
        elif kind == "step":
            steps.append(TraceStep.from_dict(rec))
    return header, steps
