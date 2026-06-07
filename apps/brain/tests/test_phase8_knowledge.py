import sys
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.main import app  # noqa: E402


class KnowledgePhase8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_knowledge_search_and_structured_entries_work(self):
        listing = self.client.get("/knowledge", params={"category": "web", "limit": 20})
        self.assertEqual(listing.status_code, 200)
        paths = [item["path"] for item in listing.json()["knowledge"]]
        self.assertIn("web/html.md", paths)
        self.assertIn("web/css.md", paths)
        self.assertIn("web/javascript.md", paths)

        search = self.client.get("/knowledge/search", params={"query": "proposal pricing approvals", "limit": 10})
        self.assertEqual(search.status_code, 200)
        search_paths = [item["path"] for item in search.json()["knowledge"]]
        self.assertTrue(any(path in {"business/proposal-writing.md", "templates/proposals.json"} for path in search_paths))

        query = self.client.get("/knowledge", params={"query": "docker deployment health checks", "limit": 5})
        self.assertEqual(query.status_code, 200)
        self.assertTrue(any(item["path"] == "devops/docker.md" for item in query.json()["knowledge"]))

    def test_knowledge_validation_analytics_and_gap_detection_work(self):
        reindex = self.client.post("/knowledge/reindex")
        self.assertEqual(reindex.status_code, 200)
        self.assertGreater(reindex.json()["indexed"], 20)

        analytics = self.client.get("/knowledge/analytics")
        self.assertEqual(analytics.status_code, 200)
        payload = analytics.json()
        self.assertGreater(payload["total_entries"], 20)
        self.assertIn("web", payload["categories"])
        self.assertGreater(payload["trusted_entries"], 10)

        validate = self.client.get("/knowledge/validate")
        self.assertEqual(validate.status_code, 200)
        self.assertTrue(validate.json()["valid"])

        gaps = self.client.get("/knowledge/gaps")
        self.assertEqual(gaps.status_code, 200)
        self.assertTrue(gaps.json()["complete"])
        self.assertEqual(gaps.json()["missing_paths"], [])

        quarantine = self.client.get("/knowledge/quarantine")
        self.assertEqual(quarantine.status_code, 200)
        self.assertEqual(quarantine.json()["knowledge"], [])

    def test_knowledge_graph_sources_and_stress_work(self):
        sources = self.client.get("/knowledge/sources")
        self.assertEqual(sources.status_code, 200)
        self.assertTrue(any(item["trusted"] for item in sources.json()["by_entry"]))

        graph = self.client.get("/knowledge/graph")
        self.assertEqual(graph.status_code, 200)
        graph_payload = graph.json()
        self.assertGreater(len(graph_payload["nodes"]), 20)
        self.assertGreater(len(graph_payload["edges"]), 5)

        pipelines = self.client.get("/knowledge/pipelines")
        self.assertEqual(pipelines.status_code, 200)
        parser_names = [item["name"] for item in pipelines.json()["parsers"]]
        self.assertIn("markdown", parser_names)
        self.assertIn("json", parser_names)

        started = time.perf_counter()
        for query in [
            "react dashboard routing",
            "wordpress handoff woocommerce",
            "sri lankan contract scope",
            "ocr confidence extraction",
            "prometheus dashboard alerts",
            "proposal timeline pricing scope",
            "fastapi websocket validation",
            "tailwind design tokens",
        ] * 5:
            response = self.client.get("/knowledge/search", params={"query": query, "limit": 6})
            self.assertEqual(response.status_code, 200)
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 8)


if __name__ == "__main__":
    unittest.main()
