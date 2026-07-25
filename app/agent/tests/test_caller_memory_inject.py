"""Voice agent formats/fetches durable caller memory for instruction inject."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

import voice_agent


class TestCallerMemoryInject(unittest.TestCase):
    def test_format_block_includes_name(self) -> None:
        text = voice_agent._format_caller_memory_block(
            {"display_name": "Darcy", "notes": ["Likes tea"], "summary": ""},
        )
        self.assertIn("Darcy", text)
        self.assertIn("Likes tea", text)

    def test_fetch_caller_memory_get(self) -> None:
        body = {"ok": True, "memory": {"display_name": "Darcy", "notes": []}}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(body).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        with patch.object(voice_agent, "_BACKEND_API", "http://127.0.0.1:8080"):
            with patch("voice_agent.urllib.request.urlopen", return_value=mock_resp):
                mem = voice_agent._fetch_caller_memory("sess-1")
        self.assertEqual(mem["display_name"], "Darcy")


if __name__ == "__main__":
    unittest.main()
