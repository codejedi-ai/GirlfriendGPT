"""Shared utilities for GirlfriendGPT."""

from .errors import (
    GirlfriendGPTError,
    ChannelError,
    ChannelConnectionError,
    ChannelSendError,
    ProviderError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ToolExecutionError,
    ToolNotFoundError,
    ContextOverflowError,
    ConfigError,
    MemoryError,
    SessionError,
    AgentError,
    ValidationError,
)

__all__ = [
    "GirlfriendGPTError",
    "ChannelError",
    "ChannelConnectionError",
    "ChannelSendError",
    "ProviderError",
    "ProviderConnectionError",
    "ProviderRateLimitError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ContextOverflowError",
    "ConfigError",
    "MemoryError",
    "SessionError",
    "AgentError",
    "ValidationError",
]
