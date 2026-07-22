"""Regression: agent JSON requires permanent LiveKit participant_id."""

from __future__ import annotations

import copy
import unittest

from agent_persona import ELLA_AGENT_ID, load_persona, make_participant_id
from agent_runtime import validate_agent_definition


class TestParticipantId(unittest.TestCase):
    def test_lena_has_permanent_participant_id(self) -> None:
        persona = load_persona(ELLA_AGENT_ID)
        pid = persona.get("participant_id")
        self.assertTrue(pid)
        self.assertFalse(any(ch.isspace() for ch in str(pid)))
        self.assertTrue(str(pid).startswith("agent-"))

    def test_validate_rejects_missing_participant_id(self) -> None:
        persona = copy.deepcopy(load_persona(ELLA_AGENT_ID))
        persona.pop("participant_id", None)
        with self.assertRaises(ValueError) as ctx:
            validate_agent_definition(persona)
        self.assertIn("participant_id", str(ctx.exception))

    def test_make_participant_id_stable(self) -> None:
        a = make_participant_id("Lena Van Der Meer", ELLA_AGENT_ID)
        b = make_participant_id("Lena Van Der Meer", ELLA_AGENT_ID)
        self.assertEqual(a, b)
        self.assertEqual(a, "agent-lena-van-der-meer-e11a0000")


if __name__ == "__main__":
    unittest.main()
