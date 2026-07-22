"""Regression: LiveKit worker name must resolve to Ella, not crash."""

from __future__ import annotations

import unittest

from agent_persona import ELLA_AGENT_ID, get_agent_definition, load_persona


class TestWorkerNamePersonaResolve(unittest.TestCase):
    def test_load_persona_worker_name_falls_back_to_ella(self) -> None:
        persona = load_persona("AI-LiveKit-Agent")
        self.assertEqual(persona["id"], ELLA_AGENT_ID)
        self.assertEqual(persona["name"], "Lena Van Der Meer")
        self.assertTrue((persona.get("instructions") or "").strip())

    def test_get_agent_definition_by_lena_name(self) -> None:
        view = get_agent_definition("Lena Van Der Meer")
        assert view is not None
        self.assertEqual(view["id"], ELLA_AGENT_ID)

    def test_load_persona_by_uuid(self) -> None:
        persona = load_persona(ELLA_AGENT_ID)
        self.assertEqual(persona["name"], "Lena Van Der Meer")
        self.assertEqual(persona["models"]["tts"]["default_language"], "en")
        web = persona["session"]["greeting_templates"]["web_session"]
        self.assertTrue(any("Lena" in g for g in web))
        self.assertFalse(any("Hoi" in g or "Hallo daar" in g for g in web))


if __name__ == "__main__":
    unittest.main()
