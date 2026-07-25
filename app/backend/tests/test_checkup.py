"""Companion check-up scheduler rings idle browsers over WS."""

from __future__ import annotations

import time
import unittest
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

from checkup import run_checkup_once
from local_events import ReachRequest, hub


@dataclass
class _FakeClient:
    client_session_id: str | None
    connected_at: float
    talk_live: bool = False
    last_checkup_at: float | None = None


class TestCheckup(unittest.IsolatedAsyncioTestCase):
    async def test_rings_idle_browser_after_initial_delay(self) -> None:
        now = time.time()
        fake = _FakeClient(
            client_session_id="sess-checkup-1",
            connected_at=now - 200,
            talk_live=False,
            last_checkup_at=None,
        )
        with patch.object(hub, "snapshot_clients", return_value=[fake]):
            with patch(
                "checkup.publish_agent_reach",
                new_callable=AsyncMock,
                return_value={"ok": True, "delivered": 1},
            ) as pub:
                with patch("checkup.checkup_enabled", return_value=True):
                    with patch("checkup.checkup_initial_seconds", return_value=120):
                        with patch("checkup.checkup_interval_seconds", return_value=600):
                            results = await run_checkup_once(now=now)

        self.assertEqual(len(results), 1)
        pub.assert_awaited_once()
        body: ReachRequest = pub.await_args.args[0]
        self.assertEqual(body.purpose, "checkup")
        self.assertEqual(body.greeting_context, "reminder_call")
        self.assertIn("checking up", body.message or "")
        self.assertIsNotNone(fake.last_checkup_at)

    async def test_skips_when_talk_live(self) -> None:
        now = time.time()
        fake = _FakeClient(
            client_session_id="sess-live",
            connected_at=now - 999,
            talk_live=True,
        )
        with patch.object(hub, "snapshot_clients", return_value=[fake]):
            with patch(
                "checkup.publish_agent_reach",
                new_callable=AsyncMock,
            ) as pub:
                with patch("checkup.checkup_enabled", return_value=True):
                    results = await run_checkup_once(now=now)
        self.assertEqual(results, [])
        pub.assert_not_awaited()

    async def test_publish_defaults_to_checkup_message(self) -> None:
        from local_events import publish_agent_reach

        with patch.object(hub, "broadcast", new_callable=AsyncMock, return_value=1) as bc:
            result = await publish_agent_reach(
                ReachRequest(
                    agent_id="e11a0000-0000-4000-8000-000000000001",
                    agent_name="Lena",
                )
            )
        event = bc.await_args.args[0]
        self.assertEqual(event["purpose"], "checkup")
        self.assertEqual(event["greeting_context"], "reminder_call")
        self.assertEqual(event["message"], "is checking up on you")
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
