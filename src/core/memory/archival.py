"""Memory archival for GirlfriendGPT - long-term memory storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import time


@dataclass
class ArchivedMemory:
    """An archived memory entry."""

    session_id: str
    summary: str
    created_at: float = field(default_factory=lambda: time.time())
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None


class MemoryArchive:
    """Long-term memory storage and retrieval.

    This class provides:
    - Archival of session summaries
    - Semantic search and recall
    - Persistent storage
    """

    def __init__(self, archive_dir: Optional[Path] = None) -> None:
        """Initialize the memory archive.

        Args:
            archive_dir: Directory for storing archives
        """
        self._archive_dir = archive_dir or Path.home() / ".gfgpt" / "memory_archive"
        self._archive_dir.mkdir(parents=True, exist_ok=True)
        self._entries: List[ArchivedMemory] = []
        self._load_archives()

    def _load_archives(self) -> None:
        """Load archived memories from disk."""
        archive_file = self._archive_dir / "archives.json"
        if archive_file.exists():
            try:
                with open(archive_file, "r") as f:
                    data = json.load(f)
                    self._entries = [
                        ArchivedMemory(**entry) for entry in data
                    ]
            except Exception as e:
                # Log but don't fail - start with empty archive
                self._entries = []

    def _save_archives(self) -> None:
        """Save archived memories to disk."""
        archive_file = self._archive_dir / "archives.json"
        try:
            with open(archive_file, "w") as f:
                data = [
                    {
                        "session_id": e.session_id,
                        "summary": e.summary,
                        "created_at": e.created_at,
                        "metadata": e.metadata,
                    }
                    for e in self._entries
                ]
                json.dump(data, f, indent=2)
        except Exception as e:
            # Log but don't fail
            pass

    async def archive(
        self,
        session_id: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ArchivedMemory:
        """Archive a session summary.

        Args:
            session_id: Session identifier
            summary: Session summary
            metadata: Optional metadata

        Returns:
            The archived memory entry
        """
        entry = ArchivedMemory(
            session_id=session_id,
            summary=summary,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        self._save_archives()
        return entry

    async def recall(
        self, query: str, top_k: int = 5
    ) -> List[ArchivedMemory]:
        """Recall archived memories relevant to a query.

        Currently uses simple keyword matching. For semantic search,
        integrate with an embedding model.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant archived memories
        """
        # Simple keyword-based ranking
        query_words = set(query.lower().split())

        scored_entries = []
        for entry in self._entries:
            text = f"{entry.summary} {entry.session_id}".lower()
            score = sum(1 for word in query_words if word in text)
            if score > 0:
                scored_entries.append((score, entry))

        # Sort by score (descending) and return top_k
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:top_k]]

    async def get_by_session_id(
        self, session_id: str
    ) -> Optional[ArchivedMemory]:
        """Get archived memory by session ID.

        Args:
            session_id: Session identifier

        Returns:
            Archived memory or None if not found
        """
        for entry in self._entries:
            if entry.session_id == session_id:
                return entry
        return None

    async def delete(self, session_id: str) -> bool:
        """Delete an archived memory.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        for i, entry in enumerate(self._entries):
            if entry.session_id == session_id:
                del self._entries[i]
                self._save_archives()
                return True
        return False

    async def get_all(self) -> List[ArchivedMemory]:
        """Get all archived memories.

        Returns:
            List of all archived memories
        """
        return self._entries.copy()

    def __len__(self) -> int:
        """Get number of archived memories."""
        return len(self._entries)

    def __repr__(self) -> str:
        return f"MemoryArchive(entries={len(self._entries)})"
