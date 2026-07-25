"""
GirlfriendGPT - AI Companion Agent with Websocket Gateway

A professional-grade AI companion framework featuring:
- WebSocket-based gateway for real-time communication
- Terminal UI (TUI) for interactive conversations
- Command-line interface (CLI) for scripting
- Configuration management under ~/.gfgpt/
- Code generation and refactoring tools
- Multiple LLM provider support

New Architecture (Domain-Driven):
- core/: Core engine (loop, context, memory)
- agents/: Agent definitions and registry
- tools/: Built-in and MCP tools
- channels/: Chat platform integrations
- providers/: LLM provider abstraction
- bus/: Message bus for events
- services/: Background services (cron, heartbeat)
- config/: Configuration management
"""

__version__ = "1.0.0"
__author__ = "Enias Cailliau"
__license__ = "MIT"

# Re-export main components for easy access
from src.config import ConfigManager
from src.core import AgentRunLoop, AgentContext
from src.tools import register_tool, get_all_tools, execute_tool
from src.bus import MessageBus, InboundMessage, OutboundMessage

__all__ = [
    # Config
    "ConfigManager",
    # Core
    "AgentRunLoop",
    "AgentContext",
    # Tools
    "register_tool",
    "get_all_tools",
    "execute_tool",
    # Bus
    "MessageBus",
    "InboundMessage",
    "OutboundMessage",
]
