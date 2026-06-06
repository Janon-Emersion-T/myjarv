import hashlib
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

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.secops import security_engine  # noqa: E402


class SecurityPhase18Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.original_require_auth = settings.SECURITY_REQUIRE_AUTH
        settings.SECURITY_REQUIRE_AUTH = True
        security_engine.unlock("Phase 18 security test setup.")
        security_engine.set_offline_mode(False, "Phase 18 security test setup.")

    @classmethod
    def tearDownClass(cls):
        security_engine.unlock("Phase 18 security test teardown.")
        security_engine.set_offline_mode(False, "Phase 18 security test teardown.")
        settings.SECURITY_REQUIRE_AUTH = cls.original_require_auth

    def _login(self) -> dict:
        response = self.client.post(
            "/auth/login",
            json={"username": settings.SECURITY_BOOTSTRAP_ADMIN, "password": settings.SECURITY_BOOTSTRAP_PASSWORD},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("access_token", payload)
        return payload

    def _headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def test_public_health_and_authenticated_identity(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")

        session = self._login()
        me = self.client.get("/auth/me", headers=self._headers(session["access_token"]))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["subject"]["username"], settings.SECURITY_BOOTSTRAP_ADMIN)

    def test_mfa_api_keys_and_secrets(self):
        user = security_engine.get_user(settings.SECURITY_BOOTSTRAP_ADMIN)
        current_bucket = int(time.time() // 30)
        code = hashlib.sha1(f"{user['mfa_secret']}:{current_bucket}".encode("utf-8")).hexdigest()[:6]
        verify = self.client.post("/auth/mfa/verify", json={"username": settings.SECURITY_BOOTSTRAP_ADMIN, "code": code})
        self.assertEqual(verify.status_code, 200)
        self.assertTrue(verify.json()["verified"])

        session = self._login()
        api_key_response = self.client.post(
            "/security/api-keys",
            headers=self._headers(session["access_token"]),
            json={"owner": settings.SECURITY_BOOTSTRAP_ADMIN, "label": f"phase18-{uuid.uuid4().hex[:6]}", "role_scope": "admin"},
        )
        self.assertEqual(api_key_response.status_code, 200)
        api_key = api_key_response.json()["api_key"]

        dashboard = self.client.get("/security/dashboard", headers={"X-API-Key": api_key})
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("compliance", dashboard.json())

        secret_name = f"phase18_secret_{uuid.uuid4().hex[:8]}"
        create_secret = self.client.post(
            "/security/secrets",
            headers=self._headers(session["access_token"]),
            json={"name": secret_name, "value": "super-secret-value", "provider": "local_vault"},
        )
        self.assertEqual(create_secret.status_code, 200)
        secrets_list = self.client.get("/security/secrets", headers=self._headers(session["access_token"]))
        self.assertEqual(secrets_list.status_code, 200)
        self.assertTrue(any(item["name"] == secret_name for item in secrets_list.json()["secrets"]))

    def test_backups_scans_metrics_and_audit_integrity(self):
        session = self._login()
        headers = self._headers(session["access_token"])

        backup = self.client.post("/security/backups", headers=headers, json={"label": "phase18-test"})
        self.assertEqual(backup.status_code, 200)
        backup_id = backup.json()["id"]

        restore = self.client.post(f"/security/backups/{backup_id}/test-restore", headers=headers)
        self.assertEqual(restore.status_code, 200)
        self.assertTrue(restore.json()["passed"])

        scan = self.client.post("/security/scans", headers=headers, json={"scan_type": "full"})
        self.assertEqual(scan.status_code, 200)
        self.assertEqual(scan.json()["status"], "completed")

        integrity = self.client.get("/security/audit-integrity", headers=headers)
        self.assertEqual(integrity.status_code, 200)
        self.assertTrue(integrity.json()["valid"])

        metrics = self.client.get("/security/metrics", headers=headers)
        self.assertEqual(metrics.status_code, 200)
        self.assertIn("security_scans_total", metrics.json())

        prometheus = self.client.get("/security/metrics?format=prometheus", headers=headers)
        self.assertEqual(prometheus.status_code, 200)
        self.assertIn("jarvis_security_incidents_total", prometheus.text)

    def test_lockdown_offline_mode_and_suspicious_request_blocking(self):
        session = self._login()
        headers = self._headers(session["access_token"])

        lockdown = self.client.post("/security/lockdown", headers=headers, json={"reason": "Phase 18 test lockdown"})
        self.assertEqual(lockdown.status_code, 200)

        blocked = self.client.post("/tasks", json={"message": "Should be blocked during lockdown"})
        self.assertEqual(blocked.status_code, 423)

        unlock = self.client.post("/security/unlock", headers=headers, json={"reason": "Phase 18 test unlock"})
        self.assertEqual(unlock.status_code, 200)

        offline = self.client.post("/security/offline-mode", headers=headers, json={"enabled": True, "reason": "Phase 18 offline"})
        self.assertEqual(offline.status_code, 200)

        offline_block = self.client.post("/tasks", json={"message": "Should be blocked in offline mode"})
        self.assertEqual(offline_block.status_code, 503)

        offline_reset = self.client.post("/security/offline-mode", headers=headers, json={"enabled": False, "reason": "Phase 18 offline reset"})
        self.assertEqual(offline_reset.status_code, 200)

        suspicious = self.client.post(
            "/memory",
            headers=headers,
            json={"scope": "agent", "key": "bad", "value": "<script>alert('x')</script>", "tags": ["phase18"]},
        )
        self.assertEqual(suspicious.status_code, 400)
        self.assertIn("issues", suspicious.json())


if __name__ == "__main__":
    unittest.main()
