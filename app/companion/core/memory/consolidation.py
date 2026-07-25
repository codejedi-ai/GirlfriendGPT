"""Memory consolidation for GirlfriendGPT - compresses old messages."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class MemoryConsolidator:
    """Compresses old messages to save context window.

    This class provides:
    - Summarization of old message sequences
    - Compression of conversation history
    - Threshold-based consolidation triggers
    """

    def __init__(self, compression_ratio: float = 0.1) -> None:
        """Initialize the consolidator.

        Args:
            compression_ratio: Target ratio of compressed to original size
        """
        self._compression_ratio = compression_ratio

    async def consolidate(
        self, messages: List[Dict[str, Any]], threshold: int = 100
    ) -> str:
        """Consolidate a list of messages into a summary.

        Args:
            messages: List of messages to consolidate
            threshold: Number of messages before consolidation triggers

        Returns:
            Consolidated summary string
        """
        if len(messages) < threshold:
            return self._quick_summary(messages)

        # For large histories, use progressive summarization
        return await self._progressive_summary(messages)

    def _quick_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Create a quick summary of messages.

        Args:
            messages: Messages to summarize

        Returns:
            Summary string
        """
        if not messages:
            return "[No conversation history]"

        # Extract key information
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        summary_parts = [
            f"Conversation with {len(user_messages)} user messages "
            f"and {len(assistant_messages)} assistant messages."
        ]

        # Add first and last message previews
        if user_messages:
            first = user_messages[0].get("content", "")[:100]
            last = user_messages[-1].get("content", "")[:100]
            summary_parts.append(f"First topic: {first}...")
            summary_parts.append(f"Last topic: {last}...")

        return "\n".join(summary_parts)

    async def _progressive_summary(
        self, messages: List[Dict[str, Any]]
    ) -> str:
        """Create a progressive summary for large histories.

        This uses a hierarchical approach:
        1. Group messages into chunks
        2. Summarize each chunk
        3. Combine chunk summaries

        Args:
            messages: Messages to summarize

        Returns:
            Progressive summary string
        """
        chunk_size = 20
        chunks = [
            messages[i : i + chunk_size]
            for i in range(0, len(messages), chunk_size)
        ]

        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            summary = self._quick_summary(chunk)
            chunk_summaries.append(f"[Segment {i + 1}] {summary}")

        return "\n\n".join(chunk_summaries)

    def should_consolidate(self, message_count: int, threshold: int) -> bool:
        """Check if consolidation should be triggered.

        Args:
            message_count: Current number of messages
            threshold: Threshold for consolidation

        Returns:
            True if consolidation should occur
        """
        return message_count > threshold

    def estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count for messages.

        Args:
            messages: Messages to estimate tokens for

        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // 4
