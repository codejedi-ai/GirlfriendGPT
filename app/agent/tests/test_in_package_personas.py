"""In-package persona catalog (self-contained, no ali-agents)."""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_paths import (
    agent_dir,
    resolve_agents_dir,
    resolve_tools_1_data,
)
from agent_persona import ELLA_AGENT_ID, load_persona


class TestInPackagePersonas(unittest.TestCase):
    def test_agents_dir_is_personas(self) -> None:
        path = resolve_agents_dir()
        self.assertEqual(path.name, "personas")
        self.assertTrue(path.is_dir())
        self.assertTrue((path / "Lena Van Der Meer.json").is_file())

    def test_tools_dir_in_package(self) -> None:
        path = resolve_tools_1_data()
        self.assertEqual(path.name, "tools")
        self.assertTrue((path / "report_adherence_intent.json").is_file())

    def test_load_ella_without_ali_agents(self) -> None:
        persona = load_persona(ELLA_AGENT_ID)
        self.assertEqual(persona["name"], "Lena Van Der Meer")
        self.assertEqual(persona["id"], ELLA_AGENT_ID)
        # Must resolve under this package, not monorepo ali-agents.
        root = agent_dir().resolve()
        self.assertTrue(str(resolve_agents_dir()).startswith(str(root)))

    def test_data_agents_symlink_points_at_personas(self) -> None:
        link = agent_dir() / "data" / "agents"
        self.assertTrue(link.exists())
        target = link.resolve()
        self.assertEqual(target, (agent_dir() / "personas").resolve())


if __name__ == "__main__":
    unittest.main()
