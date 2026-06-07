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


class BrainPhase10ApprovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def _create_critical_task(self) -> dict:
        response = self.client.post(
            "/tasks",
            json={
                "message": f"Delete production files and deploy rollback plan {uuid.uuid4().hex[:6]}",
                "requested_action": "delete production files and deploy rollback",
            },
        )
        self.assertEqual(response.status_code, 200)
        task = response.json()
        self.assertEqual(task["approval_level"], "CRITICAL")
        self.assertEqual(task["status"], "waiting_approval")
        return task

    def test_critical_chain_requires_written_signoff_and_three_stage_approval(self):
        task = self._create_critical_task()
        blocked = self.client.post(
            f"/tasks/{task['id']}/approve",
            json={"reviewer": "Ops Lead", "reviewer_role": "manager", "department": "engineering"},
        )
        self.assertEqual(blocked.status_code, 400)
        self.assertIn("Written signoff", blocked.text)

        manager = self.client.post(
            f"/tasks/{task['id']}/approve",
            json={
                "reviewer": "Ops Lead",
                "reviewer_role": "manager",
                "department": "engineering",
                "written_document": {"title": "Rollback approval", "body": "Manager signoff."},
                "evidence": [{"kind": "screenshot", "name": "plan.png"}],
            },
        )
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(manager.json()["status"], "waiting_approval")
        self.assertEqual(manager.json()["approval_summary"]["approved_count"], 1)

        director = self.client.post(
            f"/tasks/{task['id']}/approve",
            json={
                "reviewer": "Infra Director",
                "reviewer_role": "director",
                "department": "engineering",
                "written_document": {"title": "Rollback approval", "body": "Director signoff."},
            },
        )
        self.assertEqual(director.status_code, 200)
        self.assertEqual(director.json()["status"], "waiting_approval")
        self.assertEqual(director.json()["approval_summary"]["approved_count"], 2)

        executive = self.client.post(
            f"/tasks/{task['id']}/approve",
            json={
                "reviewer": "CEO",
                "reviewer_role": "executive",
                "department": "finance",
                "written_document": {"title": "Rollback approval", "body": "Executive signoff."},
                "signature": "exec-signed",
            },
        )
        self.assertEqual(executive.status_code, 200)
        payload = executive.json()
        self.assertEqual(payload["status"], "approved")
        self.assertTrue(payload["approval_summary"]["fully_approved"])
        self.assertEqual(len(payload["approvals"]), 3)

    def test_simulation_revocation_and_metrics_endpoints(self):
        task = self._create_critical_task()
        simulation = self.client.post(
            f"/tasks/{task['id']}/approvals/simulate",
            json={
                "reviewer": "Ops Lead",
                "reviewer_role": "manager",
                "department": "engineering",
                "written_document": {"title": "Simulated signoff", "body": "Preview only."},
            },
        )
        self.assertEqual(simulation.status_code, 200)
        self.assertFalse(simulation.json()["preview"]["would_fully_approve"])

        approvals = [
            {"reviewer": "Ops Lead", "reviewer_role": "manager", "department": "engineering"},
            {"reviewer": "Infra Director", "reviewer_role": "director", "department": "engineering"},
            {"reviewer": "CEO", "reviewer_role": "executive", "department": "finance"},
        ]
        latest = None
        for item in approvals:
            response = self.client.post(
                f"/tasks/{task['id']}/approve",
                json={
                    **item,
                    "written_document": {"title": "Rollback approval", "body": f"Signoff by {item['reviewer']}."},
                },
            )
            self.assertEqual(response.status_code, 200)
            latest = response.json()

        self.assertIsNotNone(latest)
        approval_id = latest["approvals"][0]["id"]
        revoked = self.client.post(
            f"/tasks/{task['id']}/approvals/{approval_id}/revoke",
            json={"actor": "Audit", "reason": "Control review reopened the task."},
        )
        self.assertEqual(revoked.status_code, 200)
        self.assertEqual(revoked.json()["status"], "waiting_approval")
        self.assertEqual(revoked.json()["approval_summary"]["revoked_count"], 1)

        queue = self.client.get("/approvals/queue")
        self.assertEqual(queue.status_code, 200)
        self.assertTrue(any(item["task_id"] == task["id"] for item in queue.json()["queue"]))

        history = self.client.get("/approvals/history", params={"task_id": task["id"], "limit": 10})
        self.assertEqual(history.status_code, 200)
        self.assertGreaterEqual(len(history.json()["approvals"]), 3)

        metrics = self.client.get("/approvals/metrics")
        self.assertEqual(metrics.status_code, 200)
        self.assertGreaterEqual(metrics.json()["revoked_total"], 1)

        archive = self.client.get("/approvals/archive")
        self.assertEqual(archive.status_code, 200)
        self.assertTrue(any(item["task_id"] == task["id"] for item in archive.json()["artifacts"]))

    def test_rejection_quarantine_and_emergency_shutdown(self):
        task = self._create_critical_task()
        rejected = self.client.post(
            f"/tasks/{task['id']}/reject",
            json={"reviewer": "Ops Lead", "notes": "Unsafe until maintenance window."},
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.json()["status"], "rejected")

        quarantine = self.client.get("/approvals/quarantine")
        self.assertEqual(quarantine.status_code, 200)
        self.assertTrue(any(item["task_id"] == task["id"] for item in quarantine.json()["artifacts"]))

        shutdown = self.client.post(
            "/approvals/emergency-shutdown",
            json={"active": True, "actor": "SecOps", "reason": "Freeze all non-manual actions."},
        )
        self.assertEqual(shutdown.status_code, 200)
        self.assertTrue(shutdown.json()["active"])

        blocked_task = self._create_critical_task()
        blocked_approval = self.client.post(
            f"/tasks/{blocked_task['id']}/approve",
            json={
                "reviewer": "Ops Lead",
                "reviewer_role": "manager",
                "department": "engineering",
                "written_document": {"title": "Rollback approval", "body": "Manager signoff."},
            },
        )
        self.assertEqual(blocked_approval.status_code, 400)
        self.assertIn("shutdown", blocked_approval.text.lower())

        reset = self.client.post(
            "/approvals/emergency-shutdown",
            json={"active": False, "actor": "SecOps", "reason": "Freeze lifted."},
        )
        self.assertEqual(reset.status_code, 200)


if __name__ == "__main__":
    unittest.main()
