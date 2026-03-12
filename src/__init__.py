"""
GirlfriendGPT - AI Companion Agent with Websocket Gateway

A professional-grade AI companion framework featuring:
- WebSocket-based gateway for real-time communication
- Terminal UI (TUI) for interactive conversations
- Command-line interface (CLI) for scripting
- Configuration management under ~/.gfgpt/
- Code generation and refactoring tools
- Multiple LLM provider support
"""

__version__ = "1.0.0"
__author__ = "Enias Cailliau"
__license__ = "MIT"

from src.config import ConfigManager

__all__ = [
    "ConfigManager",
]
