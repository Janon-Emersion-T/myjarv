import sys
import time
import unittest
import uuid
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.main import app  # noqa: E402


class RoutingPhase6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_simulation_routes_web_request_to_web_team(self):
        response = self.client.post(
            "/routing/simulate",
            json={
                "message": "Plan and build a new LKProfessionals website landing page",
                "requested_action": "website implementation",
                "metadata": {"client": "lkprofessionals", "memory_scopes": ["company", "project"]},
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent_category"], "development")
        self.assertEqual(payload["selected_agent"], "Peter")
        self.assertIn("Lara", payload["supporting_agents"])
        self.assertIn("Tony", payload["supporting_agents"])
        self.assertEqual(payload["execution_strategy"], "sequential")
        self.assertGreaterEqual(payload["confidence"], 0.88)
        self.assertIn("Jarvis", payload["review_chain"])

    def test_task_route_trace_and_reassignment_work(self):
        create = self.client.post(
            "/tasks",
            json={
                "message": f"Prepare marketing copy for a new service launch {uuid.uuid4().hex[:6]}",
                "requested_action": "draft marketing copy",
            },
        )
        self.assertEqual(create.status_code, 200)
        task = create.json()
        trace = self.client.get(f"/tasks/{task['id']}/route-trace")
        self.assertEqual(trace.status_code, 200)
        self.assertEqual(trace.json()["decision"]["selected_agent"], task["selected_agent"]["name"])

        reassign = self.client.post(
            f"/tasks/{task['id']}/reassign",
            json={"reviewer": "Janon", "agent": "Maya", "reason": "Prefer campaign owner oversight."},
        )
        self.assertEqual(reassign.status_code, 200)
        updated = reassign.json()
        self.assertEqual(updated["selected_agent"]["name"], "Maya")
        self.assertEqual(updated["routing"]["selected_agent"], "Maya")

    def test_duplicate_detection_and_replay_are_available(self):
        message = f"Review SEO plan for duplicate detection {uuid.uuid4().hex[:6]}"
        first = self.client.post("/routing/simulate", json={"message": message, "requested_action": "seo review"})
        self.assertEqual(first.status_code, 200)
        first_trace = first.json()["trace_id"]

        original = self.client.post("/tasks", json={"message": message, "requested_action": "seo review"})
        self.assertEqual(original.status_code, 200)
        original_task = original.json()

        duplicate = self.client.post("/tasks", json={"message": message, "requested_action": "seo review"})
        self.assertEqual(duplicate.status_code, 200)
        duplicate_task = duplicate.json()
        self.assertEqual(duplicate_task["routing"]["duplicate_of_task_id"], original_task["id"])

        replay = self.client.post(f"/routing/traces/{first_trace}/replay")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["mode"], "replay")

    def test_overrides_and_guardrails_affect_routing(self):
        override = self.client.post(
            "/routing/simulate",
            json={
                "message": "Need an urgent executive briefing for this week",
                "metadata": {"route_override": "Jarvis"},
            },
        )
        self.assertEqual(override.status_code, 200)
        override_payload = override.json()
        self.assertEqual(override_payload["selected_agent"], "Jarvis")

        whitelisted = self.client.post(
            "/routing/simulate",
            json={
                "message": "Build a Laravel client portal with billing workflows",
                "metadata": {"agent_whitelist": ["Lara"]},
            },
        )
        self.assertEqual(whitelisted.status_code, 200)
        whitelist_payload = whitelisted.json()
        self.assertEqual(whitelist_payload["selected_agent"], "Lara")

        dead_end = self.client.post(
            "/routing/simulate",
            json={
                "message": "Website refresh with approvals and implementation details",
                "metadata": {"agent_whitelist": ["NonexistentAgent"]},
            },
        )
        self.assertEqual(dead_end.status_code, 200)
        dead_end_payload = dead_end.json()
        self.assertEqual(dead_end_payload["selected_agent"], "Jarvis")
        self.assertTrue(dead_end_payload["is_ambiguous"])
        self.assertTrue(any("No eligible candidates remained" in warning for warning in dead_end_payload["warnings"]))

    def test_routing_analytics_and_stress_pass(self):
        started = time.perf_counter()
        for index in range(40):
            response = self.client.post(
                "/routing/simulate",
                json={"message": f"Stress route test {index} for Laravel deployment and SEO coordination"},
            )
            self.assertEqual(response.status_code, 200)
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 15)

        analytics = self.client.get("/routing/analytics")
        self.assertEqual(analytics.status_code, 200)
        payload = analytics.json()
        self.assertGreaterEqual(payload["total_traces"], 40)
        self.assertIn("development", payload["by_intent"])

        route_map = self.client.get("/routing/map")
        self.assertEqual(route_map.status_code, 200)
        self.assertTrue(any(edge["stage"] == "route:web_request" for edge in route_map.json()["edges"]))


if __name__ == "__main__":
    unittest.main()
