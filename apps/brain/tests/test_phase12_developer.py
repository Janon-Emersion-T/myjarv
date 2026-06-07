import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.main import app  # noqa: E402


class DeveloperPhase12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_repository_scan_and_health_endpoints(self):
        scan = self.client.get("/developer/scan", params={"path": "."})
        self.assertEqual(scan.status_code, 200)
        payload = scan.json()
        self.assertIn("stack", payload)
        self.assertIn("languages", payload)
        self.assertGreater(payload["total_files"], 0)

        health = self.client.get("/developer/health", params={"path": "."})
        self.assertEqual(health.status_code, 200)
        self.assertIn("score", health.json())
        self.assertIn("analysis", health.json())

        analytics = self.client.get("/developer/analytics", params={"path": "."})
        self.assertEqual(analytics.status_code, 200)
        self.assertIn("recommended_tests", analytics.json())

    def test_fix_plan_changelog_and_deployment_checklist(self):
        plan = self.client.post(
            "/developer/fix-plan",
            json={
                "goal": "Harden the approval router",
                "path": ".",
                "constraints": ["Keep backward compatibility"],
                "preferred_files": ["apps/brain/app/router.py"],
            },
        )
        self.assertEqual(plan.status_code, 200)
        self.assertIn("steps", plan.json())
        self.assertIn("recommended_tests", plan.json())

        changelog = self.client.post(
            "/developer/changelog",
            json={
                "title": "Approval hardening",
                "summary": "Improves approval routing and verification.",
                "changes": ["Added queue metrics", "Improved policy coverage"],
                "version": "1.2.3",
            },
        )
        self.assertEqual(changelog.status_code, 200)
        self.assertIn("markdown", changelog.json())
        self.assertIn("1.2.3", changelog.json()["markdown"])

        checklist = self.client.get("/developer/deployment-checklist", params={"path": "."})
        self.assertEqual(checklist.status_code, 200)
        self.assertTrue(checklist.json()["items"])


if __name__ == "__main__":
    unittest.main()
