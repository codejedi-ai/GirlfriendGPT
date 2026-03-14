"""Custom exception hierarchy for GirlfriendGPT."""

from __future__ import annotations


class GirlfriendGPTError(Exception):
    """Base exception for all GirlfriendGPT errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ChannelError(GirlfriendGPTError):
    """Channel connection or communication failure."""

    def __init__(
        self, message: str, channel_name: str | None = None, details: str | None = None
    ) -> None:
        self.channel_name = channel_name
        super().__init__(message, details)


class ChannelConnectionError(ChannelError):
    """Failed to establish channel connection."""

    pass


class ChannelSendError(ChannelError):
    """Failed to send message through channel."""

    pass


class ProviderError(GirlfriendGPTError):
    """LLM provider API failure."""

    def __init__(
        self, message: str, provider_name: str | None = None, details: str | None = None
    ) -> None:
        self.provider_name = provider_name
        super().__init__(message, details)


class ProviderConnectionError(ProviderError):
    """Failed to connect to LLM provider."""

    pass


class ProviderRateLimitError(ProviderError):
    """Rate limit exceeded for LLM provider."""

    pass


class ToolExecutionError(GirlfriendGPTError):
    """Tool execution failed."""

    def __init__(
        self, tool_name: str, reason: str, details: str | None = None
    ) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {reason}", details)


class ToolNotFoundError(GirlfriendGPTError):
    """Requested tool does not exist."""

    def __init__(self, tool_name: str, details: str | None = None) -> None:
        super().__init__(f"Tool '{tool_name}' not found", details)


class ContextOverflowError(GirlfriendGPTError):
    """Context window exceeded."""

    def __init__(self, message: str = "Context window exceeded", details: str | None = None) -> None:
        super().__init__(message, details)


class ConfigError(GirlfriendGPTError):
    """Invalid or missing configuration."""

    def __init__(
        self, key: str | None = None, message: str | None = None, details: str | None = None
    ) -> None:
        self.key = key
        msg = message or f"Invalid configuration for key: {key}" if key else "Invalid configuration"
        super().__init__(msg, details)


class MemoryError(GirlfriendGPTError):
    """Memory operation failed."""

    pass


class SessionError(GirlfriendGPTError):
    """Session management error."""

    pass


class AgentError(GirlfriendGPTError):
    """Agent execution error."""

    pass


class ValidationError(GirlfriendGPTError):
    """Input validation failed."""

    pass
