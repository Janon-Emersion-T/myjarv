import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.main import app  # noqa: E402


class WorkflowReplacementPhase14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_catalog_and_receptionist_replacement_flow(self):
        catalog = self.client.get("/workflows/replacements/catalog")
        self.assertEqual(catalog.status_code, 200)
        self.assertGreaterEqual(len(catalog.json()["catalog"]), 10)

        created = self.client.post(
            "/workflows/replacements",
            json={
                "workflow_key": "receptionist",
                "client_name": "Northstar",
                "context": "Handle inbound inquiries and appointment routing",
            },
        )
        self.assertEqual(created.status_code, 200)
        payload = created.json()
        self.assertEqual(payload["workflow_key"], "receptionist")
        self.assertTrue(payload["steps"])
        self.assertTrue(payload["approval_integrated"])
        self.assertTrue(payload["knowledge_refs"] is not None)
        self.assertTrue(payload["memory_refs"] is not None)

        details = self.client.get(f"/workflows/replacements/{payload['id']}")
        self.assertEqual(details.status_code, 200)
        self.assertEqual(details.json()["id"], payload["id"])

    def test_simulation_replay_dashboard_and_multiple_workflow_roles(self):
        roles = ["sales_assistant", "project_coordinator", "junior_developer", "seo_assistant", "content_writer", "finance_assistant", "support_assistant", "documentation_assistant", "qa_tester"]
        created_ids = []
        for role in roles:
            response = self.client.post("/workflows/replacements", json={"workflow_key": role, "context": f"Simulate {role}"})
            self.assertEqual(response.status_code, 200)
            created_ids.append(response.json()["id"])

        simulation = self.client.post(f"/workflows/replacements/{created_ids[0]}/simulate")
        self.assertEqual(simulation.status_code, 200)
        self.assertEqual(simulation.json()["status"], "simulation")
        self.assertIn("approval_mapping", simulation.json())

        replay = self.client.post(f"/workflows/replacements/{created_ids[0]}/replay")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["mode"], "replay")

        analytics = self.client.get("/workflows/replacements/analytics")
        self.assertEqual(analytics.status_code, 200)
        self.assertGreaterEqual(analytics.json()["workflows_total"], 10)

        dashboard = self.client.get("/dashboard/workflows")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("workflows", dashboard.json())
        self.assertIn("analytics", dashboard.json())


if __name__ == "__main__":
    unittest.main()
