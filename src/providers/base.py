"""Base provider abstraction for GirlfriendGPT."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, AsyncIterator


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    api_key: str = ""
    model: str = "gpt-4"
    endpoint: Optional[str] = None
    max_tokens: int = 8192
    temperature: float = 0.1
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """A chat message."""

    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None


@dataclass
class ChatResponse:
    """Response from a chat completion."""

    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None


class BaseProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers (OpenAI, Anthropic, etc.) must implement this interface
    to ensure consistent behavior across providers.

    Attributes:
        config: Provider configuration
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the provider.

        Args:
            config: Provider configuration
        """
        self.config = config

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        """Get a chat completion.

        Args:
            messages: List of chat messages
            **kwargs: Additional provider-specific options

        Returns:
            Chat response
        """
        pass

    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a chat completion.

        Args:
            messages: List of chat messages
            **kwargs: Additional provider-specific options

        Yields:
            Chunks of response content
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate the provider connection.

        Returns:
            True if connection is valid
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.config.model})"
