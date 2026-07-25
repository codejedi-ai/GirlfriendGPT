"""Agent reach-out: POST /api/agent/reach fans out over local WS."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from local_events import ReachRequest, hub, publish_agent_reach
from main import app


class TestAgentReach(unittest.IsolatedAsyncioTestCase):
    async def test_publish_voice_call_by_default(self) -> None:
        with patch.object(hub, "broadcast", new_callable=AsyncMock, return_value=1) as bc:
            result = await publish_agent_reach(
                ReachRequest(
                    agent_id="e11a0000-0000-4000-8000-000000000001",
                    agent_name="Lena Van Der Meer",
                    message="wants to talk with you",
                )
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["delivered"], 1)
        bc.assert_awaited_once()
        event = bc.await_args.args[0]
        self.assertEqual(event["type"], "voice_call")
        self.assertTrue(event["auto_answer"])
        self.assertEqual(event["agent_name"], "Lena Van Der Meer")

    async def test_publish_notify_banner_only(self) -> None:
        with patch.object(hub, "broadcast", new_callable=AsyncMock, return_value=1) as bc:
            result = await publish_agent_reach(
                ReachRequest(
                    agent_id="e11a0000-0000-4000-8000-000000000001",
                    agent_name="Lena",
                    mode="notify",
                    message="is checking in",
                )
            )
        self.assertTrue(result["ok"])
        event = bc.await_args.args[0]
        self.assertEqual(event["type"], "agent_reach")
        self.assertFalse(event["auto_answer"])

    def test_reach_http_endpoint(self) -> None:
        with patch.object(hub, "broadcast", new_callable=AsyncMock, return_value=0):
            client = TestClient(app)
            res = client.post(
                "/api/agent/reach",
                json={
                    "agent_id": "e11a0000-0000-4000-8000-000000000001",
                    "agent_name": "Lena",
                    "mode": "voice_call",
                },
            )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["event"]["type"], "voice_call")


if __name__ == "__main__":
    unittest.main()
