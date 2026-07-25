"""Regression: durable caller memory load/save/format for voice inject."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from caller_memory import (
    CallerMemoryUpdate,
    apply_update,
    format_memory_for_instructions,
    load_memory,
    memory_path,
    save_memory,
    upsert_display_name,
)
from caller_memory import CallerMemory


class TestCallerMemory(unittest.TestCase):
    def test_roundtrip_name_and_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch("caller_memory.memory_root", return_value=Path(tmp)):
                upsert_display_name("sess-abc", "Darcy")
                apply_update(
                    "sess-abc",
                    CallerMemoryUpdate(append_note="Likes tea in the evening"),
                )
                mem = load_memory("sess-abc")
                self.assertEqual(mem.display_name, "Darcy")
                self.assertIn("tea", mem.notes[0])
                self.assertTrue(memory_path("sess-abc").is_file())

    def test_format_includes_name(self) -> None:
        text = format_memory_for_instructions(
            CallerMemory(
                client_session_id="s",
                display_name="Darcy",
                notes=["Works late"],
                summary="Warm and quiet",
            )
        )
        self.assertIn("Darcy", text)
        self.assertIn("Works late", text)
        self.assertIn("Warm and quiet", text)


if __name__ == "__main__":
    unittest.main()
