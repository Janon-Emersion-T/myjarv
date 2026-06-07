import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.main import app  # noqa: E402


class ToolPhase9Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_registry_validation_and_capabilities_are_available(self):
        listing = self.client.get("/tools")
        self.assertEqual(listing.status_code, 200)
        payload = listing.json()
        self.assertTrue(payload["validation"]["valid"])
        self.assertIn("development", payload["capabilities"]["by_category"])
        self.assertTrue(any(tool["name"] == "terminal_command_tool" for tool in payload["tools"]))

        compatibility = self.client.get("/tools/compatibility")
        self.assertEqual(compatibility.status_code, 200)
        self.assertTrue(any(item["agent"] == "Jarvis" for item in compatibility.json()["matrix"]))

        adapters = self.client.get("/tools/adapters")
        self.assertEqual(adapters.status_code, 200)
        self.assertTrue(any(item["name"] == "celery" for item in adapters.json()["adapters"]))

        single = self.client.get("/tools/terminal_command_tool")
        self.assertEqual(single.status_code, 200)
        self.assertEqual(single.json()["name"], "terminal_command_tool")

    def test_tool_execution_blocking_queue_replay_and_metrics_work(self):
        read = self.client.post(
            "/tools/execute",
            json={"tool_name": "file_read", "input": {"path": "README.md"}, "actor": "Phase9Test"},
        )
        self.assertEqual(read.status_code, 200)
        read_payload = read.json()
        self.assertEqual(read_payload["status"], "completed")
        self.assertIn("Jarvis", read_payload["output"]["content"])

        blocked = self.client.post(
            "/tools/execute",
            json={
                "tool_name": "email_tool",
                "input": {"recipient": "client@example.com", "subject": "Hi", "message": "Draft only"},
                "actor": "Phase9Test",
            },
        )
        self.assertEqual(blocked.status_code, 200)
        self.assertEqual(blocked.json()["status"], "blocked")

        queued = self.client.post(
            "/tools/execute",
            json={"tool_name": "project_scanner", "input": {"path": "."}, "actor": "Phase9Test", "async_mode": True},
        )
        self.assertEqual(queued.status_code, 200)
        self.assertEqual(queued.json()["status"], "queued")

        processed = self.client.post("/tools/queue/process", params={"limit": 5})
        self.assertEqual(processed.status_code, 200)
        self.assertGreaterEqual(processed.json()["processed"], 1)

        replay = self.client.post(f"/tools/replay/{read_payload['id']}")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["status"], "completed")

        workflow = self.client.post(
            "/tools/workflows",
            json={
                "actor": "Phase9Test",
                "approved": True,
                "steps": [
                    {"tool_name": "safe_shell_plan", "input": {"goal": "Inspect repository"}},
                    {"tool_name": "proposal_generator", "input": {"brief": "Prepare a dashboard proposal"}},
                ],
            },
        )
        self.assertEqual(workflow.status_code, 200)
        self.assertEqual(workflow.json()["total"], 2)

        history = self.client.get("/tools/history", params={"limit": 20})
        self.assertEqual(history.status_code, 200)
        self.assertGreaterEqual(len(history.json()["executions"]), 4)

        analytics = self.client.get("/tools/analytics")
        self.assertEqual(analytics.status_code, 200)
        self.assertGreaterEqual(analytics.json()["total_executions"], 4)

        health = self.client.get("/tools/health")
        self.assertEqual(health.status_code, 200)
        self.assertTrue(any(item["tool_name"] == "file_read" for item in health.json()["tools"]))

        metrics = self.client.get("/tools/metrics", params={"format": "prometheus"})
        self.assertEqual(metrics.status_code, 200)
        self.assertIn("jarvis_tools_total", metrics.text)

    def test_safe_shell_command_protection_works(self):
        allowed = self.client.post(
            "/tools/execute",
            json={
                "tool_name": "terminal_command_tool",
                "input": {"command": "pwd", "cwd": "."},
                "actor": "Phase9Test",
                "approved": True,
            },
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["status"], "completed")

        blocked = self.client.post(
            "/tools/execute",
            json={
                "tool_name": "terminal_command_tool",
                "input": {"command": "rm -rf /tmp/demo", "cwd": "."},
                "actor": "Phase9Test",
                "approved": True,
            },
        )
        self.assertEqual(blocked.status_code, 200)
        self.assertIn(blocked.json()["status"], {"failed", "fallback"})


if __name__ == "__main__":
    unittest.main()
