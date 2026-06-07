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
from app.task_manager import task_manager  # noqa: E402


class SelfLearningPhase19Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_learning_pipeline_generates_reviewable_updates(self):
        success = self.client.post("/tasks", json={"message": f"Completed learning task {uuid.uuid4().hex[:6]}", "requested_action": "plan"})
        failure = self.client.post("/tasks", json={"message": f"Failed learning task {uuid.uuid4().hex[:6]}", "requested_action": "deploy"})
        self.assertEqual(success.status_code, 200)
        self.assertEqual(failure.status_code, 200)

        with task_manager._connect() as connection:  # noqa: SLF001
            connection.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (success.json()["id"],))
            connection.execute("UPDATE tasks SET status = 'failed', last_error = 'Synthetic failure for learning test' WHERE id = ?", (failure.json()["id"],))

        run = self.client.post("/learning/run", json={"limit": 80, "reviewer": "Phase19", "mode": "safe"})
        self.assertEqual(run.status_code, 200)
        self.assertIn("lessons_added", run.json())

        dashboard = self.client.get("/learning/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.json()
        self.assertIn("analytics", payload)
        self.assertGreaterEqual(payload["analytics"]["updates_total"], 1)

        updates = self.client.get("/learning/updates")
        self.assertEqual(updates.status_code, 200)
        update_id = updates.json()["updates"][0]["id"]

        review = self.client.post(f"/learning/updates/{update_id}/review", json={"reviewer": "Janon", "decision": "approved", "notes": "Looks good"})
        self.assertEqual(review.status_code, 200)
        self.assertEqual(review.json()["review_state"], "approved")

        apply = self.client.post(f"/learning/updates/{update_id}/apply", json={"reviewer": "Janon", "notes": "Apply to knowledge base"})
        self.assertEqual(apply.status_code, 200)
        self.assertEqual(apply.json()["update"]["review_state"], "applied")
        self.assertIn("semantic_diff", apply.json()["version"])


if __name__ == "__main__":
    unittest.main()
