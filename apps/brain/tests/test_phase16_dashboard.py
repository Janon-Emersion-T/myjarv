import sys
import unittest
import uuid
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.main import app  # noqa: E402


class DashboardPhase16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_dashboard_endpoints_return_operational_data(self):
        create = self.client.post(
            "/tasks",
            json={"message": f"Dashboard smoke task {uuid.uuid4().hex[:6]}", "requested_action": "plan"},
        )
        self.assertEqual(create.status_code, 200)

        summary = self.client.get("/dashboard/summary")
        self.assertEqual(summary.status_code, 200)
        self.assertIn("tasks_total", summary.json())

        reports = self.client.get("/dashboard/reports")
        self.assertEqual(reports.status_code, 200)
        self.assertIn("task_reports", reports.json())

        pipeline = self.client.get("/dashboard/pipeline")
        self.assertEqual(pipeline.status_code, 200)
        self.assertIn("stages", pipeline.json())

        kpis = self.client.get("/dashboard/kpis")
        self.assertEqual(kpis.status_code, 200)
        self.assertIn("delivery_rate", kpis.json())

        errors = self.client.get("/dashboard/errors")
        self.assertEqual(errors.status_code, 200)
        self.assertIn("failed_tasks", errors.json())

        activity = self.client.get("/dashboard/activity")
        self.assertEqual(activity.status_code, 200)
        self.assertIn("logs", activity.json())

    def test_dashboard_search_and_websocket_snapshot_work(self):
        search = self.client.get("/dashboard/search", params={"query": "Jarvis"})
        self.assertEqual(search.status_code, 200)
        self.assertIn("agents", search.json())

        with self.client.websocket_connect("/ws/dashboard") as websocket:
            packet = websocket.receive_json()
            self.assertEqual(packet["type"], "dashboard_snapshot")
            self.assertIn("summary", packet["payload"])


if __name__ == "__main__":
    unittest.main()
