"""Backend POST /api/token — frontend then connects to LiveKit."""

from __future__ import annotations

import json
import os
import unittest
from unittest import mock

from livekit_token import ELLA_AGENT_ID, build_token_payload
from main import app


class TestLiveKitTokenApi(unittest.TestCase):
    def setUp(self) -> None:
        self.env = {
            "LIVEKIT_URL": "ws://127.0.0.1:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "LIVEKIT_AGENT_NAME": "AI-LiveKit-Agent",
            "GIRLFRIENDGPT_AGENT_ID": ELLA_AGENT_ID,
        }

    def test_build_token_defaults_to_ella(self) -> None:
        with mock.patch.dict(os.environ, self.env, clear=False):
            payload = build_token_payload(greeting_context="web_session")
        self.assertTrue(payload.token)
        self.assertEqual(payload.url, "ws://127.0.0.1:7880")
        self.assertEqual(payload.agent_id, ELLA_AGENT_ID)
        self.assertEqual(payload.agent_name, "AI-LiveKit-Agent")
        self.assertEqual(payload.metadata["agent_id"], ELLA_AGENT_ID)

    def test_token_endpoint(self) -> None:
        from fastapi.testclient import TestClient

        with mock.patch.dict(os.environ, self.env, clear=False):
            client = TestClient(app)
            res = client.post(
                "/api/token",
                json={"greeting_context": "web_session", "room": "talk-test"},
            )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["room"], "talk-test")
        self.assertEqual(data["url"], "ws://127.0.0.1:7880")
        self.assertIn("token", data)
        json.dumps(data["metadata"])

    def test_connect_alias(self) -> None:
        from fastapi.testclient import TestClient

        with mock.patch.dict(os.environ, self.env, clear=False):
            client = TestClient(app)
            res = client.post("/api/connect", json={"room": "alias-room"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["room"], "alias-room")

    def test_health_names_backend(self) -> None:
        from fastapi.testclient import TestClient

        with mock.patch.dict(os.environ, self.env, clear=False):
            client = TestClient(app)
            res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["service"], "app/backend")


if __name__ == "__main__":
    unittest.main()
