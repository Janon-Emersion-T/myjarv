import json
import sys
import unittest
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.main import app  # noqa: E402


class MemoryPhase7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.memory_dir = ROOT / "data" / "memory"

    def test_memory_scopes_sidecar_files_and_search_work(self):
        suffix = uuid.uuid4().hex[:8]
        company_key = f"phase7-company-{suffix}"
        prompt_key = f"phase7-prompt-{suffix}"
        template_key = f"phase7-template-{suffix}"

        for payload in (
            {
                "scope": "company",
                "key": company_key,
                "value": "LKProfessionals keeps approved reporting language concise and executive-ready.",
                "tags": ["phase7", "company"],
                "source": "test_phase7",
                "confidence_score": 0.9,
                "importance_score": 0.9,
            },
            {
                "scope": "reusable_prompt",
                "key": prompt_key,
                "value": "Reusable prompt for monthly report drafting with summary, risks, and next steps.",
                "tags": ["phase7", "prompt"],
                "source": "test_phase7",
            },
            {
                "scope": "approved_template",
                "key": template_key,
                "value": "Approved template for client proposal follow-up and approval request.",
                "tags": ["phase7", "template"],
                "source": "test_phase7",
            },
        ):
            response = self.client.post("/memory", json=payload)
            self.assertEqual(response.status_code, 200)

        search = self.client.get("/memory/search", params={"query": "monthly report drafting"})
        self.assertEqual(search.status_code, 200)
        keys = [item["key"] for item in search.json()["memory"]]
        self.assertIn(prompt_key, keys)

        summary = self.client.get("/memory/summary")
        self.assertEqual(summary.status_code, 200)
        self.assertGreaterEqual(summary.json()["total"], 3)

        company_file = self.memory_dir / "company.json"
        prompts_file = self.memory_dir / "prompts.json"
        templates_file = self.memory_dir / "templates.json"
        self.assertTrue(company_file.exists())
        self.assertTrue(prompts_file.exists())
        self.assertTrue(templates_file.exists())

        company_records = json.loads(company_file.read_text(encoding="utf-8"))["records"]
        self.assertTrue(any(item["key"] == company_key for item in company_records))

    def test_memory_backup_snapshot_duplicates_and_cleanup_work(self):
        suffix = uuid.uuid4().hex[:8]
        duplicate_key = f"phase7-duplicate-{suffix}"
        expiry = (datetime.now(UTC) - timedelta(days=1)).isoformat()

        base = self.client.post(
            "/memory",
            json={
                "scope": "project",
                "key": duplicate_key,
                "value": "Shared duplicate candidate for deduplication checks.",
                "tags": ["phase7", "duplicate"],
                "source": "test_phase7",
                "task_id": f"task-{suffix}",
            },
        )
        self.assertEqual(base.status_code, 200)
        base_id = base.json()["id"]

        imported = self.client.post(
            "/memory/import",
            json={
                "merge": False,
                "records": [
                    {
                        "scope": "project",
                        "key": duplicate_key,
                        "value": "Shared duplicate candidate for deduplication checks.",
                        "tags": ["phase7", "duplicate"],
                        "source": "test_phase7",
                        "task_id": f"other-task-{suffix}",
                    }
                ],
            },
        )
        self.assertEqual(imported.status_code, 200)
        self.assertEqual(imported.json()["imported"], 1)

        duplicate_listing = self.client.get("/memory/duplicates")
        self.assertEqual(duplicate_listing.status_code, 200)
        self.assertTrue(any(item["key"] == duplicate_key for item in duplicate_listing.json()["duplicates"]))

        related = self.client.get(f"/memory/{base_id}/related")
        self.assertEqual(related.status_code, 200)
        self.assertGreaterEqual(len(related.json()["memory"]), 1)

        expiring = self.client.post(
            "/memory",
            json={
                "scope": "short_term",
                "key": f"phase7-expired-{suffix}",
                "value": "This short-term note should be cleaned up.",
                "tags": ["phase7", "expiry"],
                "expires_at": expiry,
            },
        )
        self.assertEqual(expiring.status_code, 200)

        snapshot = self.client.post("/memory/snapshots", json={"label": f"phase7-snapshot-{suffix}"})
        self.assertEqual(snapshot.status_code, 200)

        backup = self.client.post("/memory/backups", json={"label": f"phase7-backup-{suffix}"})
        self.assertEqual(backup.status_code, 200)
        backup_id = backup.json()["id"]

        cleanup = self.client.post("/memory/cleanup")
        self.assertEqual(cleanup.status_code, 200)
        self.assertGreaterEqual(cleanup.json()["removed"], 1)

        restore = self.client.post("/memory/backups/restore", json={"backup_id": backup_id})
        self.assertEqual(restore.status_code, 200)
        self.assertTrue(restore.json()["restored"]["merge"])

        analytics = self.client.get("/memory/analytics")
        self.assertEqual(analytics.status_code, 200)
        payload = analytics.json()
        self.assertGreaterEqual(payload["snapshots"], 1)
        self.assertGreaterEqual(payload["backups"], 1)

        adapters = self.client.get("/memory/adapters")
        self.assertEqual(adapters.status_code, 200)
        adapter_names = [item["name"] for item in adapters.json()["adapters"]]
        self.assertIn("sqlite", adapter_names)
        self.assertIn("qdrant", adapter_names)

        corrupted = self.client.get("/memory/corrupted")
        self.assertEqual(corrupted.status_code, 200)
        self.assertEqual(corrupted.json()["corrupted"], [])

        repair = self.client.post("/memory/repair")
        self.assertEqual(repair.status_code, 200)
        self.assertGreaterEqual(repair.json()["repaired"], 1)


if __name__ == "__main__":
    unittest.main()
