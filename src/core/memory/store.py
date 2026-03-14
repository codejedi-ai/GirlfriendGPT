"""Memory store for GirlfriendGPT - manages session message history."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time


@dataclass
class StoredMessage:
    """A stored message in the memory."""

    role: str
    content: str
    timestamp: float = field(default_factory=lambda: time.time())
    message_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryStore:
    """Manages session message history.

    This class provides:
    - In-memory storage of session messages
    - Retrieval of message history
    - Message appending and pruning
    """

    def __init__(self, max_messages_per_session: int = 100) -> None:
        """Initialize the memory store.

        Args:
            max_messages_per_session: Maximum messages to keep per session
        """
        self._store: Dict[str, List[StoredMessage]] = defaultdict(list)
        self._max_messages = max_messages_per_session
        self._lock = asyncio.Lock()

    async def get_history(
        self, session_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get message history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return

        Returns:
            List of messages (most recent last)
        """
        async with self._lock:
            messages = self._store.get(session_id, [])
            limited = messages[-limit:] if limit > 0 else messages
            return [self._to_dict(msg) for msg in limited]

    async def append(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append a message to session history.

        Args:
            session_id: Session identifier
            role: Message role ("user", "assistant", "system")
            content: Message content
            message_type: Type of message
            metadata: Optional metadata
        """
        async with self._lock:
            message = StoredMessage(
                role=role,
                content=content,
                message_type=message_type,
                metadata=metadata or {},
            )
            self._store[session_id].append(message)

            # Prune if over limit
            if len(self._store[session_id]) > self._max_messages:
                self._store[session_id] = self._store[session_id][
                    -self._max_messages :
                ]

    async def clear(self, session_id: Optional[str] = None) -> None:
        """Clear message history.

        Args:
            session_id: Session to clear, or None to clear all
        """
        async with self._lock:
            if session_id:
                self._store.pop(session_id, None)
            else:
                self._store.clear()

    async def get_session_ids(self) -> List[str]:
        """Get all session IDs with stored messages.

        Returns:
            List of session IDs
        """
        async with self._lock:
            return list(self._store.keys())

    async def delete_session(self, session_id: str) -> None:
        """Delete a session's message history.

        Args:
            session_id: Session to delete
        """
        async with self._lock:
            self._store.pop(session_id, None)

    def _to_dict(self, message: StoredMessage) -> Dict[str, Any]:
        """Convert StoredMessage to dictionary."""
        return {
            "role": message.role,
            "content": message.content,
            "type": message.message_type,
            "timestamp": message.timestamp,
            "metadata": message.metadata,
        }

    def __len__(self) -> int:
        """Get total number of stored messages."""
        return sum(len(msgs) for msgs in self._store.values())

    def __repr__(self) -> str:
        return f"MemoryStore(sessions={len(self._store)}, messages={len(self)})"
