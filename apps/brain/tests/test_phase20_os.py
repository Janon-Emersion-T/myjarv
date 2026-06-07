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


class OperatingSystemPhase20Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_os_dashboard_reports_and_assistants(self):
        self.client.post("/business/leads", json={"name": "OS Lead", "company": f"OS Co {uuid.uuid4().hex[:4]}", "service_interest": "automation retainer", "budget": 300000})
        self.client.post(
            "/projects",
            json={
                "name": f"OS Project {uuid.uuid4().hex[:4]}",
                "client_name": "OS Client",
                "category": "development",
                "methodology": "agile",
                "owner": "Athena",
                "summary": "Validate unified operating-system dashboard output.",
                "budget": 250000,
                "goals": ["Plan delivery", "Track approvals"],
            },
        )
        self.client.post("/learning/run", json={"limit": 50, "reviewer": "Phase20", "mode": "safe"})

        dashboard = self.client.get("/os/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.json()
        self.assertIn("modules", payload)
        self.assertIn("reports", payload)
        self.assertTrue(any(module["name"] == "learning" for module in payload["modules"]))

        assistants = self.client.get("/os/assistants")
        self.assertEqual(assistants.status_code, 200)
        self.assertTrue(any(item["assistant"] == "developer" for item in assistants.json()["assistants"]))

        daily = self.client.get("/os/reports/daily_ceo")
        weekly = self.client.get("/os/reports/weekly_strategy")
        monthly = self.client.get("/os/reports/monthly_business")
        self.assertEqual(daily.status_code, 200)
        self.assertEqual(weekly.status_code, 200)
        self.assertEqual(monthly.status_code, 200)
        self.assertEqual(daily.json()["type"], "daily_ceo")
        self.assertEqual(weekly.json()["type"], "weekly_strategy")
        self.assertEqual(monthly.json()["type"], "monthly_business")


if __name__ == "__main__":
    unittest.main()
