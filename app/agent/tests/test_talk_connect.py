"""Talk gateway connect payload embeds agent dispatch metadata."""

from __future__ import annotations

import json
import os
import unittest
from unittest import mock

from talk.server import ELLA_AGENT_ID, app, build_connect_payload


class TestTalkConnect(unittest.TestCase):
    def setUp(self) -> None:
        self.env = {
            "LIVEKIT_URL": "ws://127.0.0.1:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "LIVEKIT_AGENT_NAME": "AI-LiveKit-Agent",
            "GIRLFRIENDGPT_AGENT_ID": ELLA_AGENT_ID,
        }

    def test_build_connect_payload_defaults_to_ella(self) -> None:
        with mock.patch.dict(os.environ, self.env, clear=False):
            payload = build_connect_payload(greeting_context="web_session")
        self.assertTrue(payload.token)
        self.assertEqual(payload.url, "ws://127.0.0.1:7880")
        self.assertEqual(payload.agent_id, ELLA_AGENT_ID)
        self.assertEqual(payload.agent_name, "AI-LiveKit-Agent")
        self.assertEqual(payload.metadata["agent_id"], ELLA_AGENT_ID)
        self.assertEqual(payload.metadata["greeting_context"], "web_session")
        self.assertTrue(payload.room.startswith("talk-"))

    def test_token_http_endpoint(self) -> None:
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
        self.assertEqual(data["agent_id"], ELLA_AGENT_ID)
        self.assertIn("token", data)
        self.assertIn("url", data)
        # Backend returns credentials only — frontend connects to LiveKit.
        self.assertEqual(data["url"], "ws://127.0.0.1:7880")
        meta = data["metadata"]
        self.assertEqual(meta["agent_id"], ELLA_AGENT_ID)
        json.dumps(meta)

    def test_connect_alias_same_as_token(self) -> None:
        from fastapi.testclient import TestClient

        with mock.patch.dict(os.environ, self.env, clear=False):
            client = TestClient(app)
            res = client.post(
                "/api/connect",
                json={"greeting_context": "web_session", "room": "talk-alias"},
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["room"], "talk-alias")

    def test_health(self) -> None:
        from fastapi.testclient import TestClient

        with mock.patch.dict(os.environ, self.env, clear=False):
            client = TestClient(app)
            res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["default_agent_id"], ELLA_AGENT_ID)


if __name__ == "__main__":
    unittest.main()
