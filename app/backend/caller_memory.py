"""Durable caller memory — written-down facts the companion reloads on connect.

Short-term memory = soft LiveKit session reuse (same room / AgentSession still up).
Long-term memory = this store (name + notes + summary), injected into instructions
on each cold start.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def memory_root() -> Path:
    raw = (Path.home() / ".gfgpt" / "voice_memory").expanduser()
    return raw


def _safe_key(client_session_id: str) -> str:
    key = re.sub(r"[^a-zA-Z0-9._-]+", "_", (client_session_id or "").strip())[:80]
    return key or "anonymous"


@dataclass
class CallerMemory:
    client_session_id: str
    display_name: str = ""
    notes: list[str] = field(default_factory=list)
    summary: str = ""
    updated_at: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.updated_at = time.time()


class CallerMemoryUpdate(BaseModel):
    display_name: str | None = None
    summary: str | None = None
    notes: list[str] | None = None
    append_note: str | None = None


def memory_path(client_session_id: str) -> Path:
    return memory_root() / f"{_safe_key(client_session_id)}.json"


def load_memory(client_session_id: str) -> CallerMemory:
    csid = (client_session_id or "").strip()
    path = memory_path(csid)
    if not path.is_file():
        return CallerMemory(client_session_id=csid)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return CallerMemory(client_session_id=csid)
    notes = raw.get("notes") or []
    if not isinstance(notes, list):
        notes = []
    return CallerMemory(
        client_session_id=str(raw.get("client_session_id") or csid),
        display_name=str(raw.get("display_name") or "").strip(),
        notes=[str(n).strip() for n in notes if str(n).strip()],
        summary=str(raw.get("summary") or "").strip(),
        updated_at=float(raw.get("updated_at") or time.time()),
    )


def save_memory(mem: CallerMemory) -> CallerMemory:
    mem.touch()
    root = memory_root()
    root.mkdir(parents=True, exist_ok=True)
    path = memory_path(mem.client_session_id)
    path.write_text(json.dumps(asdict(mem), indent=2), encoding="utf-8")
    return mem


def apply_update(client_session_id: str, body: CallerMemoryUpdate) -> CallerMemory:
    mem = load_memory(client_session_id)
    if body.display_name is not None:
        name = body.display_name.strip()
        if name:
            mem.display_name = name
    if body.summary is not None:
        mem.summary = body.summary.strip()
    if body.notes is not None:
        mem.notes = [str(n).strip() for n in body.notes if str(n).strip()]
    note = (body.append_note or "").strip()
    if note:
        mem.notes.append(note)
        # Cap so local prompts stay small
        mem.notes = mem.notes[-40:]
    return save_memory(mem)


def upsert_display_name(client_session_id: str, display_name: str) -> CallerMemory:
    return apply_update(
        client_session_id,
        CallerMemoryUpdate(display_name=display_name),
    )


def format_memory_for_instructions(mem: CallerMemory) -> str:
    """Block appended to persona instructions so she knows who is calling."""
    lines = ["## Who you are talking to (persistent memory — do not forget)"]
    name = (mem.display_name or "").strip()
    if name:
        lines.append(f"- Their name is {name}. Use it naturally.")
    else:
        lines.append("- Their name is not known yet; ask once warmly if needed.")
    if mem.summary.strip():
        lines.append(f"- Standing summary: {mem.summary.strip()}")
    if mem.notes:
        lines.append("- Things you have written down about them:")
        for note in mem.notes[-12:]:
            lines.append(f"  - {note}")
    lines.append(
        "Treat this block as true for this call. "
        "If they correct a fact, remember the correction."
    )
    return "\n".join(lines)


def memory_to_dict(mem: CallerMemory) -> dict[str, Any]:
    return asdict(mem)
