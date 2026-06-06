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


class CollaborationPhase15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_development_task_executes_with_collaboration_session(self):
        create = self.client.post(
            "/tasks",
            json={
                "message": f"Build a Laravel website with SEO and security review {uuid.uuid4().hex[:6]}",
                "requested_action": "implementation plan",
                "metadata": {"client": "lkprofessionals", "memory_scopes": ["company", "project", "client"]},
            },
        )
        self.assertEqual(create.status_code, 200)
        task = create.json()
        if task["approval_level"] != "LOW":
            approve = self.client.post(
                f"/tasks/{task['id']}/approve",
                json={"reviewer": "Janon", "notes": "Approved for collaboration test."},
            )
            self.assertEqual(approve.status_code, 200)
        execute = self.client.post(
            f"/tasks/{task['id']}/execute",
            json={"executor": "Jarvis", "force_retry": False},
        )
        self.assertEqual(execute.status_code, 200)
        executed = execute.json()
        result = executed["execution_result"]
        self.assertIsNotNone(result["collaboration_session_id"])
        self.assertGreaterEqual(result["contribution_count"], 2)
        self.assertTrue(result["collaboration_timeline"])
        self.assertTrue(result["review_chain_results"])

        collaboration = self.client.get(f"/tasks/{task['id']}/collaboration")
        self.assertEqual(collaboration.status_code, 200)
        session = collaboration.json()
        self.assertEqual(session["id"], result["collaboration_session_id"])
        self.assertGreaterEqual(len(session["contributions"]), 2)
        self.assertGreaterEqual(len(session["messages"]), 2)

    def test_collaboration_plan_replay_and_analytics(self):
        create = self.client.post(
            "/tasks",
            json={
                "message": f"Prepare finance and legal review for a website proposal {uuid.uuid4().hex[:6]}",
                "requested_action": "proposal review",
            },
        )
        self.assertEqual(create.status_code, 200)
        task = create.json()
        plan = self.client.post(f"/tasks/{task['id']}/collaboration/plan")
        self.assertEqual(plan.status_code, 200)
        planned_session = plan.json()
        self.assertEqual(planned_session["mode"], "simulation")
        self.assertTrue(planned_session["participants"])

        replay = self.client.post(f"/collaboration/sessions/{planned_session['id']}/replay")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["mode"], "replay")

        analytics = self.client.get("/collaboration/analytics")
        self.assertEqual(analytics.status_code, 200)
        payload = analytics.json()
        self.assertGreaterEqual(payload["total_sessions"], 1)

    def test_websocket_stream_receives_collaboration_event(self):
        create = self.client.post(
            "/tasks",
            json={
                "message": f"Draft content strategy with SEO review {uuid.uuid4().hex[:6]}",
                "requested_action": "content strategy",
            },
        )
        self.assertEqual(create.status_code, 200)
        task = create.json()
        plan = self.client.post(f"/tasks/{task['id']}/collaboration/plan")
        session = plan.json()
        with self.client.websocket_connect(f"/ws/collaboration/{session['id']}") as websocket:
            first = websocket.receive_json()
            self.assertEqual(first["type"], "connected")
            second = websocket.receive_json()
            self.assertEqual(second["type"], "snapshot")
            self.assertEqual(second["payload"]["id"], session["id"])


if __name__ == "__main__":
    unittest.main()
