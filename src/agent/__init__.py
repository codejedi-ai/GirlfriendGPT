"""AI Influencer Agent - SmolAgent implementation.

DEPRECATED: Use src.core and src.agents instead.
This module is kept for backward compatibility.
"""

from .agent import Agent, Config, SmolAgent, AgentConfig

__all__ = ["Agent", "Config", "SmolAgent", "AgentConfig"]

# Re-export from new locations for backward compatibility
try:
    from ..core import AgentRunLoop, AgentContext
    from ..tools import register_tool, get_all_tools, execute_tool
except ImportError:
    pass
