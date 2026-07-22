"""Regression: JobRequest accept uses persona participant_id."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest import mock

from agent_persona import ELLA_AGENT_ID, load_persona
from voice_agent import _on_job_request, _resolve_agent_id_from_meta


class TestJobAcceptIdentity(unittest.IsolatedAsyncioTestCase):
    def test_resolve_agent_id_from_metadata(self) -> None:
        aid = _resolve_agent_id_from_meta({"agent_id": ELLA_AGENT_ID})
        self.assertEqual(aid, ELLA_AGENT_ID)

    async def test_on_job_request_accepts_with_participant_id(self) -> None:
        persona = load_persona(ELLA_AGENT_ID)
        expected = persona["participant_id"]
        accepted: dict = {}

        class FakeReq:
            job = SimpleNamespace(
                metadata=json.dumps({"agent_id": ELLA_AGENT_ID, "greeting_context": "web_session"})
            )
            room = SimpleNamespace(name="voice-test")

            async def accept(self, **kwargs):
                accepted.update(kwargs)

        with mock.patch("voice_agent.load_persona", return_value=persona):
            await _on_job_request(FakeReq())
        self.assertEqual(accepted.get("identity"), expected)
        self.assertEqual(accepted.get("name"), persona["name"])


if __name__ == "__main__":
    unittest.main()
