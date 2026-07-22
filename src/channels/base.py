"""Base channel abstraction for GirlfriendGPT."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..bus.events import InboundMessage, OutboundMessage


@dataclass
class ChannelConfig:
    """Configuration for a channel."""

    enabled: bool = True
    allow_from: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseChannel(ABC):
    """Abstract base class for all communication channels.

    All channels (Telegram, WhatsApp, Discord, etc.) must implement this interface
    to ensure consistent behavior across platforms.

    Attributes:
        config: Channel configuration
        bus: Message bus for publishing/subscribing to messages
        enabled: Whether the channel is enabled
    """

    def __init__(self, config: dict, bus: "MessageBus") -> None:
        """Initialize the channel.

        Args:
            config: Channel configuration dictionary
            bus: Message bus instance for event publishing
        """
        self.config = config
        self.bus = bus
        self.enabled = config.get("enabled", True)
        self._allow_from = config.get("allowFrom", [])

    @abstractmethod
    async def start(self) -> None:
        """Start listening for messages.

        This method should initialize the channel connection and begin
        processing incoming messages.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Graceful shutdown.

        This method should cleanly close connections and release resources.
        """
        pass

    @abstractmethod
    async def send(self, message: OutboundMessage) -> None:
        """Send a message to the platform.

        Args:
            message: The outbound message to send
        """
        pass

    async def publish_inbound(self, message: InboundMessage) -> None:
        """Publish an inbound message to the message bus.

        Args:
            message: The inbound message to publish
        """
        await self.bus.publish(message)

    def is_allowed(self, sender_id: str) -> bool:
        """Check if a sender is allowed to interact.

        Args:
            sender_id: The ID of the message sender

        Returns:
            True if the sender is allowed, False otherwise
        """
        if not self._allow_from:
            return True
        return sender_id in self._allow_from

    @property
    def name(self) -> str:
        """Get the channel name."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(enabled={self.enabled})"
