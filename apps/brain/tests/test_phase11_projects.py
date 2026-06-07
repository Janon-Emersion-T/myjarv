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


class ProjectManagerPhase11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_project_creation_and_management_flow(self):
        response = self.client.post(
            "/projects",
            json={
                "name": f"Portal Launch {uuid.uuid4().hex[:6]}",
                "client_name": "Northstar Holdings",
                "category": "development",
                "methodology": "agile",
                "owner": "Athena",
                "summary": "Deliver the first portal release with approvals and QA gates.",
                "deadline": "2026-06-30T00:00:00+00:00",
                "budget": 850000,
                "goals": [
                    "Create approved delivery plan",
                    "Implement backend and dashboard work",
                    "Run QA and production release review",
                ],
                "departments": ["development", "operations", "finance"],
            },
        )
        self.assertEqual(response.status_code, 200)
        project = response.json()
        self.assertEqual(project["methodology"], "agile")
        self.assertTrue(project["tasks"])
        self.assertTrue(project["timeline"])

        milestone = self.client.post(
            f"/projects/{project['id']}/milestones",
            json={"title": "Discovery signoff", "due_date": "2026-06-15T00:00:00+00:00", "owner": "Athena"},
        )
        self.assertEqual(milestone.status_code, 200)
        self.assertEqual(len(milestone.json()["milestones"]), 1)

        blocker = self.client.post(
            f"/projects/{project['id']}/blockers",
            json={"title": "Client credentials missing", "severity": "high", "owner": "Athena", "notes": "Waiting on admin access."},
        )
        self.assertEqual(blocker.status_code, 200)
        self.assertEqual(len(blocker.json()["blockers"]), 1)
        self.assertGreaterEqual(blocker.json()["risk_score"], 40)

        worklog = self.client.post(
            f"/projects/{project['id']}/worklogs",
            json={"contributor": "Taylor", "hours": 4.5, "summary": "Prepared UI delivery slices.", "task_title": "Dashboard shell"},
        )
        self.assertEqual(worklog.status_code, 200)
        self.assertEqual(worklog.json()["contributor"], "Taylor")

        dependency = self.client.post(
            f"/projects/{project['id']}/dependencies",
            json={"title": "QA depends on staging build", "depends_on": "staging-build", "type_": "release"},
        )
        self.assertEqual(dependency.status_code, 200)
        self.assertEqual(len(dependency.json()["dependencies"]), 1)

        details = self.client.get(f"/projects/{project['id']}")
        self.assertEqual(details.status_code, 200)
        payload = details.json()
        self.assertEqual(payload["client_name"], "Northstar Holdings")
        self.assertTrue(payload["playbooks"] is not None)

    def test_project_reports_analytics_and_dashboard(self):
        create = self.client.post(
            "/projects",
            json={
                "name": f"SEO Retainer {uuid.uuid4().hex[:6]}",
                "client_name": "Growth Labs",
                "category": "marketing",
                "methodology": "kanban",
                "owner": "Athena",
                "summary": "Coordinate the monthly SEO retainer program and reporting.",
                "deadline": "2026-07-20T00:00:00+00:00",
                "budget": 240000,
                "goals": ["Run SEO audit", "Publish monthly insights", "Review competitor changes"],
                "departments": ["marketing", "operations"],
            },
        )
        self.assertEqual(create.status_code, 200)
        project_id = create.json()["id"]

        for report_type in ("daily", "weekly", "client", "invoice"):
            report = self.client.post(f"/projects/{project_id}/reports/{report_type}")
            self.assertEqual(report.status_code, 200)
            self.assertEqual(report.json()["type"], report_type)
            self.assertIn("summary", report.json())

        analytics = self.client.get("/projects/analytics")
        self.assertEqual(analytics.status_code, 200)
        self.assertGreaterEqual(analytics.json()["projects_total"], 1)
        self.assertIn("burndown", analytics.json())

        dashboard = self.client.get("/dashboard/projects")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("projects", dashboard.json())
        self.assertIn("analytics", dashboard.json())


if __name__ == "__main__":
    unittest.main()
