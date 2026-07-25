"""Core engine for GirlfriendGPT - main agent loop and context management."""

from .loop import AgentRunLoop
from .context import AgentContext

__all__ = ["AgentRunLoop", "AgentContext"]
