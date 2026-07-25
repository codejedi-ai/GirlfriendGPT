"""Regression: Streamlit chron draws inexact delays and POSTs checkup reach."""

from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from utils.checkup_cron import (
    CronConfig,
    in_quiet_hours,
    invoke_checkup,
    next_delay_seconds,
)


class TestCheckupCron(unittest.TestCase):
    def test_next_delay_is_random_within_range(self) -> None:
        cfg = CronConfig(min_minutes=10, max_minutes=20, jitter_frac=0.0, respect_quiet_hours=False)
        rng = __import__("random").Random(42)
        samples = [next_delay_seconds(cfg, rng=rng) for _ in range(30)]
        self.assertTrue(all(10 * 60 <= s <= 20 * 60 for s in samples))
        # Not all identical — randomness matters
        self.assertGreater(len(set(round(s) for s in samples)), 1)

    def test_jitter_makes_exact_bounds_inexact(self) -> None:
        cfg = CronConfig(min_minutes=30, max_minutes=30, jitter_frac=0.2, respect_quiet_hours=False)
        rng = __import__("random").Random(7)
        samples = [next_delay_seconds(cfg, rng=rng) for _ in range(40)]
        # With jitter, some draws leave the exact 30m center
        self.assertTrue(any(abs(s - 1800) > 1 for s in samples))
        self.assertTrue(all(s >= 30 for s in samples))

    def test_quiet_hours_wrap_midnight(self) -> None:
        cfg = CronConfig(quiet_start_hour=23, quiet_end_hour=7, respect_quiet_hours=True)
        self.assertTrue(in_quiet_hours(cfg, now=datetime(2026, 7, 21, 23, 30)))
        self.assertTrue(in_quiet_hours(cfg, now=datetime(2026, 7, 22, 3, 0)))
        self.assertFalse(in_quiet_hours(cfg, now=datetime(2026, 7, 22, 10, 0)))

    def test_invoke_posts_checkup_payload(self) -> None:
        cfg = CronConfig(
            backend_url="http://127.0.0.1:8080",
            agent_id="e11a0000-0000-4000-8000-000000000001",
            agent_name="Lena Van Der Meer",
        )
        mock_res = MagicMock()
        mock_res.json.return_value = {"ok": True, "delivered": 1}
        mock_res.raise_for_status = MagicMock()
        mock_session = MagicMock()
        mock_session.post.return_value = mock_res

        result = invoke_checkup(cfg, session=mock_session)
        self.assertTrue(result["ok"])
        args, kwargs = mock_session.post.call_args
        self.assertIn("/api/agent/reach", args[0])
        payload = kwargs["json"]
        self.assertEqual(payload["purpose"], "checkup")
        self.assertEqual(payload["greeting_context"], "reminder_call")
        self.assertEqual(payload["mode"], "voice_call")


if __name__ == "__main__":
    unittest.main()
