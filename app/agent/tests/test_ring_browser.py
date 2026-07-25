"""Regression: voice worker can ring the local UI via POST /api/agent/reach."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

import voice_agent


class TestRingBrowser(unittest.TestCase):
    def test_ring_posts_voice_call(self) -> None:
        body = {"ok": True, "delivered": 1}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(body).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False

        with patch.object(voice_agent, "_BACKEND_API", "http://127.0.0.1:8080"):
            with patch("voice_agent.urllib.request.urlopen", return_value=mock_resp) as open_mock:
                result = voice_agent.ring_browser_for_voice(
                    agent_id="e11a0000-0000-4000-8000-000000000001",
                    agent_name="Lena Van Der Meer",
                )

        self.assertTrue(result["ok"])
        req = open_mock.call_args.args[0]
        self.assertIn("/api/agent/reach", req.full_url)
        payload = json.loads(req.data.decode("utf-8"))
        self.assertEqual(payload["mode"], "voice_call")
        self.assertTrue(payload["auto_answer"])


if __name__ == "__main__":
    unittest.main()
