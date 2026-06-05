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


class BrainPhase4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["version"], "0.3.0")

    def test_memory_round_trip(self):
        key = f"phase4-memory-{uuid.uuid4().hex[:8]}"
        response = self.client.post(
            "/memory",
            json={
                "scope": "project",
                "key": key,
                "value": "Phase 4 memory verification record.",
                "tags": ["phase4", "test"],
                "source": "test_phase4",
            },
        )
        self.assertEqual(response.status_code, 200)
        created = response.json()
        self.assertEqual(created["key"], key)

        listing = self.client.get("/memory", params={"scope": "project", "limit": 20})
        self.assertEqual(listing.status_code, 200)
        keys = [item["key"] for item in listing.json()["memory"]]
        self.assertIn(key, keys)

    def test_low_risk_task_executes_end_to_end(self):
        create_response = self.client.post(
            "/tasks",
            json={
                "message": f"Create a content calendar outline for LKProfessionals {uuid.uuid4().hex[:6]}",
                "requested_action": "plan",
            },
        )
        self.assertEqual(create_response.status_code, 200)
        task = create_response.json()
        self.assertIn(task["status"], {"routed", "waiting_approval"})

        execute_response = self.client.post(
            f"/tasks/{task['id']}/execute",
            json={"executor": "Jarvis", "force_retry": False},
        )
        self.assertEqual(execute_response.status_code, 200)
        executed = execute_response.json()
        self.assertEqual(executed["status"], "completed")
        self.assertIsNotNone(executed["execution_result"])
        self.assertIsNotNone(executed["review_result"])
        history_statuses = [entry["status"] for entry in executed["history"]]
        self.assertIn("received", history_statuses)
        self.assertIn("routed", history_statuses)
        self.assertIn("executing", history_statuses)
        self.assertIn("completed", history_statuses)

    def test_high_risk_task_requires_approval_then_executes(self):
        create_response = self.client.post(
            "/tasks",
            json={
                "message": f"Prepare invoice follow-up and finance review {uuid.uuid4().hex[:6]}",
                "requested_action": "email invoice follow-up",
            },
        )
        self.assertEqual(create_response.status_code, 200)
        task = create_response.json()
        self.assertEqual(task["status"], "waiting_approval")

        blocked_execute = self.client.post(
            f"/tasks/{task['id']}/execute",
            json={"executor": "Jarvis", "force_retry": False},
        )
        self.assertEqual(blocked_execute.status_code, 409)

        approve_response = self.client.post(
            f"/tasks/{task['id']}/approve",
            json={"reviewer": "Janon", "notes": "Approved for phase 4 test."},
        )
        self.assertEqual(approve_response.status_code, 200)
        approved = approve_response.json()
        self.assertEqual(approved["status"], "approved")

        execute_response = self.client.post(
            f"/tasks/{task['id']}/execute",
            json={"executor": "Jarvis", "force_retry": False},
        )
        self.assertEqual(execute_response.status_code, 200)
        executed = execute_response.json()
        self.assertEqual(executed["status"], "completed")
        history_statuses = [entry["status"] for entry in executed["history"]]
        self.assertIn("approved", history_statuses)
        self.assertIn("executing", history_statuses)
        self.assertIn("completed", history_statuses)


if __name__ == "__main__":
    unittest.main()
