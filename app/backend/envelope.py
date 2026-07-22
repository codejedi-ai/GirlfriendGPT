"""Message envelopes — every queue payload is one of these.

Channel adapters never put bespoke shapes on the queue; they construct an
``InboundEnvelope`` and ``XADD`` it. Sub-agents publish ``OutboundEnvelope``s
back to ``agents:replies`` and adapters fan them out by ``target_channel``.

The ``trust`` field is the loyalty hook (see design §4): admin channels
(FastAPI, CLI) declare ``TrustLevel.ADMIN``; user channels (Telegram,
Discord, browser-term) declare ``TrustLevel.USER``. The dispatcher enforces
privileged actions on ``trust == ADMIN``.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TrustLevel(str, Enum):
    """Channel-declared trust. Enforced by the dispatcher, not the adapter."""

    ADMIN = "admin"
    USER = "user"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    # ULID-shaped enough for v0.1: time prefix + random suffix. Replace with
    # a real ULID library when we wire Redis Streams (Streams give us its own
    # message id; this is for the application-level message_id).
    return f"{int(_utcnow().timestamp() * 1000):013d}-{secrets.token_hex(6)}"


@dataclass
class InboundEnvelope:
    """A message arriving from a channel adapter, bound for an agent."""

    source_channel: str
    source_address: str
    trust: TrustLevel
    payload: dict[str, Any]
    message_id: str = field(default_factory=_new_id)
    correlation_id: str = field(default_factory=_new_id)
    enqueued_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["trust"] = self.trust.value
        d["enqueued_at"] = self.enqueued_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "InboundEnvelope":
        return cls(
            source_channel=d["source_channel"],
            source_address=d["source_address"],
            trust=TrustLevel(d["trust"]),
            payload=d["payload"],
            message_id=d["message_id"],
            correlation_id=d["correlation_id"],
            enqueued_at=datetime.fromisoformat(d["enqueued_at"]),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass
class OutboundEnvelope:
    """A reply from an agent, bound for a channel adapter."""

    in_reply_to: str
    target_channel: str
    target_address: str
    payload: dict[str, Any]
    sent_at: datetime = field(default_factory=_utcnow)
    # If non-None, names the promoted artifact (workflow_id or "trace:<sid>")
    # that produced this reply. Surfaces in the UX as
    # "Reusing learned workflow X". See VERIFY criterion 3.
    harness_hit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["sent_at"] = self.sent_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "OutboundEnvelope":
        return cls(
            in_reply_to=d["in_reply_to"],
            target_channel=d["target_channel"],
            target_address=d["target_address"],
            payload=d["payload"],
            sent_at=datetime.fromisoformat(d["sent_at"]),
            harness_hit=d.get("harness_hit"),
        )
