"""Agent definitions and registry for GirlfriendGPT."""

from .registry import AgentRegistry
from .subagent import Subagent

__all__ = ["AgentRegistry", "Subagent"]
