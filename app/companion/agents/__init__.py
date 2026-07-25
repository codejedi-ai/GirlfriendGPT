"""Agent definitions and registry for GirlfriendGPT."""

from .json_catalog import (
    CLI_AGENT_ID,
    CLI_DISPLAY_NAME,
    get_cli_agent_definition,
    list_cli_agents,
    load_cli_agent,
)
from .registry import AgentRegistry
from .subagent import Subagent

__all__ = [
    "AgentRegistry",
    "Subagent",
    "CLI_AGENT_ID",
    "CLI_DISPLAY_NAME",
    "get_cli_agent_definition",
    "list_cli_agents",
    "load_cli_agent",
]
