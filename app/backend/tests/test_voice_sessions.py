"""Voice session reuse: remint tokens into the same tracked room."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from livekit_token import ELLA_AGENT_ID, build_token_payload
from main import app
import voice_sessions as vs


class TestVoiceSessions(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.env = {
            "LIVEKIT_URL": "ws://127.0.0.1:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "LIVEKIT_AGENT_NAME": "AI-LiveKit-Agent",
            "GIRLFRIENDGPT_AGENT_ID": ELLA_AGENT_ID,
            "VOICE_SESSION_IDLE_SECONDS": "1800",
            "GFGPT_STATE_DIR": self._tmpdir.name,
        }
        self._env_patch = mock.patch.dict(os.environ, self.env, clear=False)
        self._env_patch.start()
        vs.clear_sessions()

    def tearDown(self) -> None:
        vs.clear_sessions()
        self._env_patch.stop()
        self._tmpdir.cleanup()

    async def test_cold_start_dispatches(self) -> None:
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
        sess = vs.get_session("sess-aaaa-bbbb", ELLA_AGENT_ID)
        assert sess is not None
        self.assertEqual(sess.mint_count, 1)
        self.assertIsNotNone(sess.last_token_id)
        self.assertIsNotNone(sess.last_token_expires_at)
        self.assertEqual(payload.expiry_state, "active")
        self.assertGreater(payload.expires_at or 0, payload.issued_at or 0)

    async def test_reuse_skips_dispatch_when_agent_present(self) -> None:
        pid = vs.resolve_agent_participant_id(ELLA_AGENT_ID)
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
        # Second connect same session → same room, new mint counted
        with mock.patch.object(vs, "list_room_identities", return_value=[pid]):
            again = await vs.connect_voice_session(
                client_session_id="sess-aaaa-bbbb",
                agent_id=ELLA_AGENT_ID,
                mint_token=build_token_payload,
            )
        self.assertEqual(again["payload"].room, result["payload"].room)
        self.assertTrue(again["reused"])
        self.assertEqual(vs.get_session("sess-aaaa-bbbb", ELLA_AGENT_ID).mint_count, 2)

    async def test_remint_keeps_same_room_when_agent_gone(self) -> None:
        """Agent left → remint still uses tracked room (no random talk-uuid)."""
        with mock.patch.object(vs, "list_room_identities", return_value=[]):
            first = await vs.connect_voice_session(
                client_session_id="sess-stable-room",
                agent_id=ELLA_AGENT_ID,
                mint_token=build_token_payload,
            )
            second = await vs.connect_voice_session(
                client_session_id="sess-stable-room",
                agent_id=ELLA_AGENT_ID,
                mint_token=build_token_payload,
            )
        self.assertEqual(first["payload"].room, second["payload"].room)
        self.assertFalse(first["reused"])
        self.assertFalse(second["reused"])
        self.assertEqual(vs.get_session("sess-stable-room", ELLA_AGENT_ID).mint_count, 2)

    async def test_registry_survives_reload_from_disk(self) -> None:
        with mock.patch.object(vs, "list_room_identities", return_value=[]):
            first = await vs.connect_voice_session(
                client_session_id="sess-persist",
                agent_id=ELLA_AGENT_ID,
                mint_token=build_token_payload,
            )
        room = first["payload"].room
        # Simulate backend restart: clear memory, reload from disk
        vs._sessions.clear()
        vs._loaded = False
        restored = vs.get_session("sess-persist", ELLA_AGENT_ID)
        assert restored is not None
        self.assertEqual(restored.room_id, room)
        self.assertTrue(Path(self._tmpdir.name, "voice_sessions.json").is_file())
        self.assertTrue(Path(self._tmpdir.name, "token_mints.jsonl").is_file())

    async def test_idle_hard_end_deletes_session(self) -> None:
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

    def test_voice_sessions_list(self) -> None:
        with mock.patch.object(vs, "list_room_identities", return_value=[]):
            client = TestClient(app)
            client.post(
                "/api/token",
                json={
                    "client_session_id": "list-me",
                    "agent_id": ELLA_AGENT_ID,
                    "greeting_context": "web_session",
                },
            )
            res = client.get("/api/voice-sessions")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertGreaterEqual(body["count"], 1)
        rooms = [s["room_id"] for s in body["sessions"]]
        self.assertTrue(any(r.startswith("voice-") for r in rooms))
        self.assertIn("last_token_expiry_state", body["sessions"][0])

    def test_rooms_and_mints_track_expiry(self) -> None:
        with mock.patch.object(vs, "list_room_identities", return_value=[]):
            client = TestClient(app)
            tok = client.post(
                "/api/token",
                json={
                    "client_session_id": "mint-log",
                    "agent_id": ELLA_AGENT_ID,
                    "greeting_context": "web_session",
                },
            )
            self.assertEqual(tok.status_code, 200)
            data = tok.json()
            self.assertEqual(data["expiry_state"], "active")
            self.assertTrue(data["token_id"])
            rooms = client.get("/api/rooms").json()
            mints = client.get("/api/token-mints").json()
        self.assertGreaterEqual(rooms["count"], 1)
        self.assertEqual(rooms["rooms"][0]["last_token_expiry_state"], "active")
        self.assertGreaterEqual(mints["count"], 1)
        mint = mints["mints"][0]
        self.assertEqual(mint["expiry_state"], "active")
        self.assertIn("expires_at", mint)
        self.assertEqual(mint["token_id"], data["token_id"])

    def test_expiry_state_flips_after_ttl(self) -> None:
        self.assertEqual(vs.expiry_state_for(time.time() + 60), "active")
        self.assertEqual(vs.expiry_state_for(time.time() - 1), "expired")

    def test_explicit_room_still_works(self) -> None:
        client = TestClient(app)
        res = client.post(
            "/api/token",
            json={"room": "talk-test", "greeting_context": "web_session"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["room"], "talk-test")
        rooms = vs.list_rooms()
        self.assertTrue(any(r["room_id"] == "talk-test" for r in rooms))
        mints = vs.list_mints(limit=5)
        self.assertTrue(any(m["room_id"] == "talk-test" for m in mints))


if __name__ == "__main__":
    unittest.main()
