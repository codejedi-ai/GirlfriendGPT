"""Voice session reuse: reconnect without re-dispatch when agent is present."""

from __future__ import annotations

import os
import time
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from livekit_token import ELLA_AGENT_ID, build_token_payload
from main import app
import voice_sessions as vs


class TestVoiceSessions(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        vs.clear_sessions()
        self.env = {
            "LIVEKIT_URL": "ws://127.0.0.1:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "LIVEKIT_AGENT_NAME": "AI-LiveKit-Agent",
            "GIRLFRIENDGPT_AGENT_ID": ELLA_AGENT_ID,
            "VOICE_SESSION_IDLE_SECONDS": "1800",
        }

    async def test_cold_start_dispatches(self) -> None:
        with mock.patch.dict(os.environ, self.env, clear=False):
            with mock.patch.object(vs, "list_room_identities", return_value=[]):
                result = await vs.connect_voice_session(
                    client_session_id="sess-aaaa-bbbb",
                    agent_id=ELLA_AGENT_ID,
                    mint_token=build_token_payload,
                )
        self.assertFalse(result["reused"])
        self.assertEqual(result["agent_state"], "starting")
        payload = result["payload"]
        self.assertTrue(payload.room.startswith("voice-"))
        self.assertIn("agent_id", payload.metadata)

    async def test_reuse_skips_dispatch_when_agent_present(self) -> None:
        pid = vs.resolve_agent_participant_id(ELLA_AGENT_ID)
        with mock.patch.dict(os.environ, self.env, clear=False):
            with mock.patch.object(
                vs, "list_room_identities", return_value=[pid, "user-sessaaaa"]
            ):
                result = await vs.connect_voice_session(
                    client_session_id="sess-aaaa-bbbb",
                    agent_id=ELLA_AGENT_ID,
                    mint_token=build_token_payload,
                )
        self.assertTrue(result["reused"])
        self.assertEqual(result["agent_state"], "running")
        # Second connect same session → same room
        with mock.patch.object(vs, "list_room_identities", return_value=[pid]):
            again = await vs.connect_voice_session(
                client_session_id="sess-aaaa-bbbb",
                agent_id=ELLA_AGENT_ID,
                mint_token=build_token_payload,
            )
        self.assertEqual(again["payload"].room, result["payload"].room)
        self.assertTrue(again["reused"])

    async def test_idle_hard_end_deletes_session(self) -> None:
        with mock.patch.dict(os.environ, self.env, clear=False):
            with mock.patch.object(vs, "list_room_identities", return_value=[]):
                await vs.connect_voice_session(
                    client_session_id="sess-idle-test",
                    agent_id=ELLA_AGENT_ID,
                    mint_token=build_token_payload,
                )
            sess = vs.get_session("sess-idle-test", ELLA_AGENT_ID)
            assert sess is not None
            sess.last_human_at = time.time() - 2000
            with mock.patch.object(vs, "list_room_identities", return_value=[]):
                with mock.patch.object(vs, "delete_livekit_room", return_value=None) as dele:
                    ended = await vs.sweep_idle_sessions(now=time.time())
                    dele.assert_awaited()
            self.assertIn(sess.room_id, ended)
            self.assertIsNone(vs.get_session("sess-idle-test", ELLA_AGENT_ID))

    def test_token_endpoint_passes_client_session(self) -> None:
        with mock.patch.dict(os.environ, self.env, clear=False):
            with mock.patch.object(vs, "list_room_identities", return_value=[]):
                client = TestClient(app)
                res = client.post(
                    "/api/token",
                    json={
                        "greeting_context": "web_session",
                        "client_session_id": "frontend-session-1",
                        "agent_id": ELLA_AGENT_ID,
                    },
                )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["client_session_id"], "frontend-session-1")
        self.assertIn("reused", data)
        self.assertTrue(data["room"].startswith("voice-"))
        self.assertFalse(data["reused"])

    def test_explicit_room_still_works(self) -> None:
        with mock.patch.dict(os.environ, self.env, clear=False):
            client = TestClient(app)
            res = client.post(
                "/api/token",
                json={"room": "talk-test", "greeting_context": "web_session"},
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["room"], "talk-test")


if __name__ == "__main__":
    unittest.main()
