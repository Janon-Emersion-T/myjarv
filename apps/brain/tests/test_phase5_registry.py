import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.agents.registry import get_agent_by_name, get_registry_snapshot, list_department_groups  # noqa: E402
from app.main import app  # noqa: E402


class RegistryPhase5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_registry_snapshot_contains_department_groups(self):
        snapshot = get_registry_snapshot()
        self.assertIn("version", snapshot)
        self.assertIn("departments", snapshot)
        self.assertIn("agents", snapshot)
        self.assertGreaterEqual(len(snapshot["departments"]), 1)
        self.assertEqual(len(snapshot["agents"]), 102)

    def test_get_agent_by_name_accepts_slug(self):
        agent = get_agent_by_name("jarvis")
        self.assertEqual(agent.name, "Jarvis")
        self.assertEqual(agent.slug, "jarvis")

    def test_department_groups_are_available(self):
        groups = list_department_groups()
        self.assertGreaterEqual(len(groups), 1)
        self.assertTrue(any(group.slug == "development" for group in groups))

    def test_agents_endpoint_exposes_grouped_registry_data(self):
        response = self.client.get("/agents")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("departments", payload)
        self.assertIn("agents", payload)
        self.assertEqual(payload["version"], "2.0.0")

    def test_registry_endpoint_returns_full_snapshot(self):
        response = self.client.get("/agents/registry")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("source_company_structure", payload)
        self.assertEqual(len(payload["agents"]), 102)


if __name__ == "__main__":
    unittest.main()
