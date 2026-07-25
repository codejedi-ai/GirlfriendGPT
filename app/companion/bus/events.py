"""Event definitions for the message bus."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from enum import Enum


class EventType(str, Enum):
    """Types of events in the system."""

    INBOUND_MESSAGE = "inbound_message"
    OUTBOUND_MESSAGE = "outbound_message"
    AGENT_RESPONSE = "agent_response"
    TOOL_EXECUTION = "tool_execution"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    ERROR = "error"
    SYSTEM = "system"


@dataclass
class Event:
    """Base event class."""

    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: __import__("time").time())
    source: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "source": self.source,
        }


@dataclass
class InboundMessage:
    """Represents an inbound message from a channel."""

    session_id: str
    content: str
    sender_id: str
    channel: str
    message_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: __import__("time").time())

    def to_event(self) -> Event:
        """Convert to bus event."""
        return Event(
            type=EventType.INBOUND_MESSAGE,
            data={
                "session_id": self.session_id,
                "content": self.content,
                "sender_id": self.sender_id,
                "message_type": self.message_type,
                "metadata": self.metadata,
            },
            source=self.channel,
            timestamp=self.timestamp,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "content": self.content,
            "sender_id": self.sender_id,
            "channel": self.channel,
            "message_type": self.message_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class OutboundMessage:
    """Represents an outbound message to a channel."""

    session_id: str
    content: str
    channel: str
    message_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[str] = None

    def to_event(self) -> Event:
        """Convert to bus event."""
        return Event(
            type=EventType.OUTBOUND_MESSAGE,
            data={
                "session_id": self.session_id,
                "content": self.content,
                "message_type": self.message_type,
                "metadata": self.metadata,
                "reply_to": self.reply_to,
            },
            source=self.channel,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "content": self.content,
            "channel": self.channel,
            "message_type": self.message_type,
            "metadata": self.metadata,
            "reply_to": self.reply_to,
        }
