"""Agent context management for GirlfriendGPT."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentContext:
    """Manages the context for an agent interaction.

    This class handles:
    - Session state
    - Message history
    - Tool execution results
    - Metadata
    """

    session_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(
        self, role: str, content: str, message_type: str = "text"
    ) -> None:
        """Add a message to the context.

        Args:
            role: Message role ("user", "assistant", "system")
            content: Message content
            message_type: Type of message ("text", "code", "image", etc.)
        """
        self.messages.append(
            {"role": role, "content": content, "type": message_type}
        )

    def add_user_message(self, content: str) -> None:
        """Add a user message to the context."""
        self.add_message("user", content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the context."""
        self.add_message("assistant", content)

    def add_system_message(self, content: str) -> None:
        """Add a system message to the context."""
        self.add_message("system", content)

    def add_tool_result(
        self, tool_name: str, result: Any, success: bool = True
    ) -> None:
        """Add a tool execution result.

        Args:
            tool_name: Name of the tool
            result: Tool execution result
            success: Whether the tool execution was successful
        """
        self.tool_results.append(
            {
                "tool_name": tool_name,
                "result": result,
                "success": success,
            }
        )

    def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages from the context.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        return self.messages[-limit:]

    def get_full_history(self) -> List[Dict[str, Any]]:
        """Get full message history.

        Returns:
            All messages in the context
        """
        return self.messages.copy()

    def clear(self) -> None:
        """Clear the context."""
        self.messages.clear()
        self.tool_results.clear()
        self.metadata.clear()

    def to_prompt(self) -> str:
        """Convert context to a prompt string.

        Returns:
            Formatted prompt string
        """
        lines = []
        for msg in self.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def __len__(self) -> int:
        """Get the number of messages in the context."""
        return len(self.messages)

    def __repr__(self) -> str:
        return f"AgentContext(session_id={self.session_id}, messages={len(self.messages)})"
