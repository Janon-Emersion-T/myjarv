from __future__ import annotations

import hashlib
import json
import re
import secrets
import sqlite3
import tarfile
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agents.registry import get_agent_by_name
from app.config import ROOT_DIR, settings
from app.logger import logger
from app.secops.tokens import issue_token, verify_token
from app.secops.vault import decrypt_bytes, decrypt_text, encrypt_bytes, encrypt_text


ROLE_POLICIES: dict[str, set[str]] = {
    "admin": {"*"},
    "operator": {
        "dashboard.read",
        "task.read",
        "task.execute",
        "task.approve",
        "task.reject",
        "memory.read",
        "voice.use",
        "security.read",
        "backup.create",
    },
    "developer": {
        "dashboard.read",
        "task.read",
        "task.execute",
        "routing.read",
        "collaboration.read",
        "voice.use",
        "security.read",
        "scan.run",
    },
    "auditor": {"dashboard.read", "task.read", "security.read", "scan.read", "backup.read"},
    "viewer": {"dashboard.read", "task.read", "memory.read"},
}

PATH_ACTIONS = {
    "/dashboard": "dashboard.read",
    "/tasks": "task.read",
    "/memory": "memory.read",
    "/routing": "routing.read",
    "/collaboration": "collaboration.read",
    "/voice": "voice.use",
    "/security": "security.read",
}

VAULT_PROVIDERS = [
    {"name": "local_vault", "kind": "encrypted", "configured": True, "description": "Built-in encrypted local secret vault."},
    {"name": "environment", "kind": "plaintext_env", "configured": True, "description": "Reads secrets from environment variables as a safe fallback."},
    {
        "name": "hashicorp_vault",
        "kind": "external",
        "configured": bool(getattr(settings, "HASHICORP_VAULT_ADDR", None)),
        "description": "HashiCorp Vault integration placeholder for future external secret management.",
    },
    {
        "name": "cloud_secret_manager",
        "kind": "external",
        "configured": bool(getattr(settings, "CLOUD_SECRET_MANAGER_ENDPOINT", None)),
        "description": "Cloud secret manager integration placeholder for future provider adapters.",
    },
]


class SecurityEngine:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir = Path(settings.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._lockdown = False
        self._offline_mode = False
        self._init_db()
        self._bootstrap_admin()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS security_users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    department TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    mfa_secret TEXT,
                    attributes_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS security_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    expires_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS security_api_keys (
                    id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    hashed_key TEXT NOT NULL,
                    encrypted_key TEXT NOT NULL,
                    role_scope TEXT NOT NULL,
                    attributes_json TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS security_secrets (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    encrypted_value TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS security_events (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_hash TEXT,
                    event_hash TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS security_backups (
                    id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    encrypted INTEGER NOT NULL DEFAULT 1,
                    size_bytes INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    restore_tested INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(security_events)").fetchall()}
            if "previous_hash" not in columns:
                connection.execute("ALTER TABLE security_events ADD COLUMN previous_hash TEXT")
            if "event_hash" not in columns:
                connection.execute("ALTER TABLE security_events ADD COLUMN event_hash TEXT")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS security_incidents (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS security_scans (
                    id TEXT PRIMARY KEY,
                    scan_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    findings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
        self._migrate_event_hashes()

    def _bootstrap_admin(self) -> None:
        username = settings.SECURITY_BOOTSTRAP_ADMIN
        with self._connect() as connection:
            existing = connection.execute("SELECT id FROM security_users WHERE username = ?", (username,)).fetchone()
            if existing:
                return
            now = self._now()
            connection.execute(
                """
                INSERT INTO security_users (id, username, password_hash, role, department, is_active, mfa_secret, attributes_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    username,
                    self._hash_password(settings.SECURITY_BOOTSTRAP_PASSWORD),
                    "admin",
                    "executive",
                    self._totp_secret(),
                    json.dumps({"clearance": "critical", "departments": ["all"], "environment": settings.APP_ENV}),
                    now,
                    now,
                ),
            )
        self.record_event("iam", "INFO", username, "Bootstrapped security admin.", {"role": "admin"})

    def login(self, username: str, password: str, ip_address: str | None = None, user_agent: str | None = None) -> dict[str, Any]:
        user = self.get_user(username)
        if not self._verify_password(password, user["password_hash"]):
            self.record_event("auth", "WARNING", username, "Failed login attempt.", {"ip_address": ip_address})
            raise ValueError("Invalid credentials.")
        token = issue_token(
            {
                "sub": user["id"],
                "username": user["username"],
                "role": user["role"],
                "department": user["department"],
                "type": "access",
            },
            settings.SECURITY_SECRET_KEY,
            expires_in=3600,
        )
        session_id = str(uuid.uuid4())
        expires_at = datetime.fromtimestamp(self._epoch() + 3600, UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO security_sessions (id, user_id, token, ip_address, user_agent, expires_at, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (session_id, user["id"], token, ip_address, user_agent, expires_at, self._now()),
            )
        self.record_event("auth", "INFO", username, "Login successful.", {"session_id": session_id})
        return {
            "session_id": session_id,
            "access_token": token,
            "token_type": "bearer",
            "role": user["role"],
            "department": user["department"],
            "mfa_required": bool(user["mfa_secret"]),
        }

    def verify_mfa(self, username: str, code: str) -> dict[str, Any]:
        user = self.get_user(username)
        if not user["mfa_secret"]:
            return {"verified": True, "method": "disabled"}
        if not self._verify_totp(user["mfa_secret"], code):
            raise ValueError("Invalid MFA code.")
        self.record_event("auth", "INFO", username, "MFA verified.", {})
        return {"verified": True, "method": "totp"}

    def logout(self, token: str) -> dict[str, Any]:
        payload = verify_token(token, settings.SECURITY_SECRET_KEY)
        with self._connect() as connection:
            connection.execute("UPDATE security_sessions SET is_active = 0 WHERE token = ?", (token,))
        self.record_event("auth", "INFO", payload["username"], "Session logged out.", {})
        return {"logged_out": True}

    def get_user(self, username: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM security_users WHERE username = ?", (username,)).fetchone()
        if row is None:
            raise ValueError("User not found.")
        return self._row_to_user(row)

    def authenticate_token(self, token: str) -> dict[str, Any]:
        payload = verify_token(token, settings.SECURITY_SECRET_KEY)
        with self._connect() as connection:
            session = connection.execute(
                "SELECT is_active FROM security_sessions WHERE token = ? ORDER BY created_at DESC LIMIT 1",
                (token,),
            ).fetchone()
        if session is None or not bool(session["is_active"]):
            raise ValueError("Inactive session.")
        return payload

    def create_api_key(self, owner: str, label: str, role_scope: str = "viewer", attributes: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_key = f"jarvis_{secrets.token_urlsafe(24)}"
        key_id = str(uuid.uuid4())
        encrypted_key = encrypt_text(raw_key, settings.SECURITY_SECRET_KEY)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO security_api_keys (id, owner_id, label, hashed_key, encrypted_key, role_scope, attributes_json, is_active, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, NULL)
                """,
                (
                    key_id,
                    owner,
                    label,
                    self._hash_string(raw_key),
                    encrypted_key,
                    role_scope,
                    json.dumps(attributes or {}),
                    self._now(),
                ),
            )
        self.record_event("apikey", "INFO", owner, "Created API key.", {"label": label, "role_scope": role_scope})
        return {"id": key_id, "label": label, "role_scope": role_scope, "api_key": raw_key}

    def validate_api_key(self, raw_key: str) -> dict[str, Any]:
        hashed = self._hash_string(raw_key)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM security_api_keys WHERE hashed_key = ? AND is_active = 1",
                (hashed,),
            ).fetchone()
        if row is None:
            raise ValueError("Invalid API key.")
        with self._connect() as connection:
            connection.execute(
                "UPDATE security_api_keys SET last_used_at = ? WHERE id = ?",
                (self._now(), row["id"]),
            )
        return dict(row) | {"attributes": json.loads(row["attributes_json"])}

    def list_api_keys(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, owner_id, label, role_scope, is_active, created_at, last_used_at FROM security_api_keys ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def put_secret(self, name: str, value: str, provider: str = "local_vault") -> dict[str, Any]:
        existing = self.get_secret(name, decrypt=False)
        now = self._now()
        if existing:
            version = existing["version"] + 1
            with self._connect() as connection:
                connection.execute(
                    "UPDATE security_secrets SET encrypted_value = ?, provider = ?, version = ?, updated_at = ? WHERE name = ?",
                    (encrypt_text(value, settings.SECURITY_SECRET_KEY), provider, version, now, name),
                )
        else:
            version = 1
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO security_secrets (id, name, encrypted_value, provider, version, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        name,
                        encrypt_text(value, settings.SECURITY_SECRET_KEY),
                        provider,
                        version,
                        now,
                        now,
                    ),
                )
        self.record_event("vault", "INFO", "system", "Stored secret.", {"name": name, "provider": provider, "version": version})
        return {"name": name, "provider": provider, "version": version}

    def get_secret(self, name: str, decrypt: bool = True) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM security_secrets WHERE name = ?", (name,)).fetchone()
        if row is None:
            return None
        data = dict(row)
        if decrypt:
            data["value"] = decrypt_text(row["encrypted_value"], settings.SECURITY_SECRET_KEY)
        return data

    def list_secrets(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT name, provider, version, created_at, updated_at FROM security_secrets ORDER BY name ASC").fetchall()
        return [dict(row) for row in rows]

    def list_vault_providers(self) -> list[dict[str, Any]]:
        return VAULT_PROVIDERS

    def authorize(self, subject: dict[str, Any], action: str, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
        attributes = attributes or {}
        role = subject.get("role", "viewer")
        allowed = "*" in ROLE_POLICIES.get(role, set()) or action in ROLE_POLICIES.get(role, set())
        if not allowed:
            return {"allowed": False, "reason": f"Role {role} lacks {action}."}
        if attributes.get("risk_level") == "CRITICAL" and role != "admin":
            return {"allowed": False, "reason": "Critical actions require admin clearance."}
        if attributes.get("department") and subject.get("department") not in {attributes["department"], "executive"} and role != "admin":
            return {"allowed": False, "reason": "Department policy denied access."}
        return {"allowed": True, "reason": "Authorized by RBAC and ABAC checks."}

    def enforce_path(self, subject: dict[str, Any], path: str, method: str) -> None:
        for prefix, action in PATH_ACTIONS.items():
            if path.startswith(prefix):
                result = self.authorize(subject, action, {"path": path, "method": method})
                if not result["allowed"]:
                    raise PermissionError(result["reason"])

    def check_agent_permissions(self, agent_name: str, requested_action: str | None = None) -> dict[str, Any]:
        agent = get_agent_by_name(agent_name)
        blocked = False
        reasons = []
        if agent.risk_level == "CRITICAL":
            blocked = True
            reasons.append("Critical-risk agent actions always require executive review.")
        if requested_action and "delete" in requested_action.lower():
            blocked = True
            reasons.append("Delete actions are restricted by agent policy.")
        return {
            "agent": agent.name,
            "department": agent.company_department,
            "approval_level": agent.approval_level,
            "blocked": blocked,
            "reasons": reasons,
        }

    def create_backup(self, label: str = "manual") -> dict[str, Any]:
        backup_id = str(uuid.uuid4())
        target = self.backup_dir / f"{backup_id}.tar.enc"
        with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as handle:
            tar_path = Path(handle.name)
        with tarfile.open(tar_path, "w") as archive:
            self._add_backup_tree(archive, ROOT_DIR / "data", "data")
            self._add_backup_file(archive, ROOT_DIR / "packages" / "agents" / "registry.json", "packages/agents/registry.json")
            self._add_backup_file(archive, ROOT_DIR / ".env.example", ".env.example")
        raw = tar_path.read_bytes()
        encrypted, _ = encrypt_bytes(raw, settings.SECURITY_SECRET_KEY)
        target.write_bytes(encrypted)
        checksum = hashlib.sha256(encrypted).hexdigest()
        size = target.stat().st_size
        tar_path.unlink(missing_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO security_backups (id, label, file_path, encrypted, size_bytes, checksum, restore_tested, created_at)
                VALUES (?, ?, ?, 1, ?, ?, 0, ?)
                """,
                (backup_id, label, str(target), size, checksum, self._now()),
            )
        self.record_event("backup", "INFO", "system", "Created encrypted backup.", {"backup_id": backup_id, "label": label})
        return {"id": backup_id, "label": label, "file_path": str(target), "size_bytes": size, "checksum": checksum}

    def restore_backup(self, backup_id: str) -> dict[str, Any]:
        backup = self.get_backup(backup_id)
        raw = Path(backup["file_path"]).read_bytes()
        restored = decrypt_bytes(raw, settings.SECURITY_SECRET_KEY)
        with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as handle:
            tar_path = Path(handle.name)
        tar_path.write_bytes(restored)
        restore_dir = self.backup_dir / f"restore-{backup_id}"
        restore_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tar_path, "r") as archive:
            archive.extractall(restore_dir, filter="data")
        tar_path.unlink(missing_ok=True)
        with self._connect() as connection:
            connection.execute(
                "UPDATE security_backups SET restore_tested = 1 WHERE id = ?",
                (backup_id,),
            )
        self.record_event("recovery", "INFO", "system", "Restored encrypted backup.", {"backup_id": backup_id, "restore_dir": str(restore_dir)})
        return {"backup_id": backup_id, "restore_dir": str(restore_dir), "status": "restored"}

    def test_backup_restore(self, backup_id: str) -> dict[str, Any]:
        restored = self.restore_backup(backup_id)
        restore_dir = Path(restored["restore_dir"])
        checks = {
            "data_present": (restore_dir / "data").exists(),
            "registry_present": (restore_dir / "packages" / "agents" / "registry.json").exists(),
            "env_example_present": (restore_dir / ".env.example").exists(),
        }
        passed = all(checks.values())
        self.record_event(
            "recovery",
            "INFO" if passed else "HIGH",
            "system",
            "Completed automated restore test.",
            {"backup_id": backup_id, "checks": checks, "passed": passed},
        )
        return {"backup_id": backup_id, "passed": passed, "checks": checks, "restore_dir": str(restore_dir)}

    def list_backups(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM security_backups ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def get_backup(self, backup_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM security_backups WHERE id = ?", (backup_id,)).fetchone()
        if row is None:
            raise ValueError("Backup not found.")
        return dict(row)

    def run_scan(self, scan_type: str = "full") -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        findings.extend(self._scan_secrets())
        findings.extend(self._scan_dependencies())
        findings.extend(self._scan_repository())
        findings.extend(self._scan_shell_risks())
        record = {
            "id": str(uuid.uuid4()),
            "scan_type": scan_type,
            "status": "completed",
            "findings_json": json.dumps(findings),
            "created_at": self._now(),
        }
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO security_scans (id, scan_type, status, findings_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (record["id"], record["scan_type"], record["status"], record["findings_json"], record["created_at"]),
            )
        if any(item["severity"] in {"HIGH", "CRITICAL"} for item in findings):
            self.create_incident("Security scan findings detected", json.dumps(findings)[:2000], "HIGH")
        self.record_event("scan", "INFO", "system", "Completed security scan.", {"scan_id": record["id"], "finding_count": len(findings)})
        return {"id": record["id"], "scan_type": scan_type, "status": "completed", "findings": findings}

    def list_scans(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM security_scans ORDER BY created_at DESC").fetchall()
        return [dict(row) | {"findings": json.loads(row["findings_json"])} for row in rows]

    def create_incident(self, title: str, details: str, severity: str = "HIGH") -> dict[str, Any]:
        incident = {
            "id": str(uuid.uuid4()),
            "status": "open",
            "severity": severity,
            "title": title,
            "details": details,
            "created_at": self._now(),
        }
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO security_incidents (id, status, severity, title, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                tuple(incident.values()),
            )
        self.record_event("incident", severity, "system", title, {"details": details[:500]})
        return incident

    def list_incidents(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM security_incidents ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def lockdown(self, reason: str) -> dict[str, Any]:
        self._lockdown = True
        self.record_event("lockdown", "CRITICAL", "system", "Emergency lockdown activated.", {"reason": reason})
        return {"locked": True, "reason": reason}

    def unlock(self, reason: str) -> dict[str, Any]:
        self._lockdown = False
        self.record_event("lockdown", "INFO", "system", "Emergency lockdown released.", {"reason": reason})
        return {"locked": False, "reason": reason}

    def set_offline_mode(self, enabled: bool, reason: str) -> dict[str, Any]:
        self._offline_mode = enabled
        self.record_event("offline_mode", "HIGH" if enabled else "INFO", "system", "Security offline mode toggled.", {"enabled": enabled, "reason": reason})
        return {"offline_mode": enabled, "reason": reason}

    def is_lockdown_active(self) -> bool:
        return self._lockdown

    def is_offline_mode(self) -> bool:
        return self._offline_mode

    def compliance_report(self) -> dict[str, Any]:
        integrity = self.verify_audit_log_integrity()
        return {
            "environment": settings.APP_ENV,
            "audit_logs": True,
            "audit_log_integrity": integrity["valid"],
            "production_lock_mode": settings.PRODUCTION_LOCK_MODE,
            "auth_required": settings.SECURITY_REQUIRE_AUTH,
            "vault_enabled": True,
            "vault_providers": [provider["name"] for provider in self.list_vault_providers()],
            "backups": len(self.list_backups()),
            "scans": len(self.list_scans()),
            "incidents": len(self.list_incidents()),
        }

    def dashboard(self) -> dict[str, Any]:
        events = self.list_events(limit=100)
        severe = [event for event in events if event["severity"] in {"HIGH", "CRITICAL"}]
        return {
            "users": self.list_users(),
            "api_keys": self.list_api_keys(),
            "secrets": self.list_secrets(),
            "backups": self.list_backups(),
            "scans": self.list_scans(),
            "incidents": self.list_incidents(),
            "recent_events": events[:50],
            "alerts": severe[:20],
            "compliance": self.compliance_report(),
            "lockdown_active": self._lockdown,
            "offline_mode": self._offline_mode,
        }

    def metrics(self) -> dict[str, Any]:
        incidents = self.list_incidents()
        scans = self.list_scans()
        events = self.list_events(limit=500)
        backups = self.list_backups()
        integrity = self.verify_audit_log_integrity()
        return {
            "users_total": len(self.list_users()),
            "api_keys_total": len(self.list_api_keys()),
            "secrets_total": len(self.list_secrets()),
            "backups_total": len(backups),
            "backups_restore_tested_total": sum(1 for item in backups if item["restore_tested"]),
            "security_scans_total": len(scans),
            "security_incidents_total": len(incidents),
            "security_alerts_total": sum(1 for event in events if event["severity"] in {"HIGH", "CRITICAL"}),
            "lockdown_active": int(self._lockdown),
            "offline_mode_active": int(self._offline_mode),
            "audit_log_integrity_valid": int(integrity["valid"]),
        }

    def prometheus_metrics(self) -> str:
        metrics = self.metrics()
        lines = [
            "# HELP jarvis_security_users_total Total configured security users.",
            "# TYPE jarvis_security_users_total gauge",
            f"jarvis_security_users_total {metrics['users_total']}",
            "# HELP jarvis_security_api_keys_total Total active and inactive API keys.",
            "# TYPE jarvis_security_api_keys_total gauge",
            f"jarvis_security_api_keys_total {metrics['api_keys_total']}",
            "# HELP jarvis_security_incidents_total Total tracked security incidents.",
            "# TYPE jarvis_security_incidents_total gauge",
            f"jarvis_security_incidents_total {metrics['security_incidents_total']}",
            "# HELP jarvis_security_alerts_total High and critical security events.",
            "# TYPE jarvis_security_alerts_total gauge",
            f"jarvis_security_alerts_total {metrics['security_alerts_total']}",
            "# HELP jarvis_security_lockdown_active Current lockdown state.",
            "# TYPE jarvis_security_lockdown_active gauge",
            f"jarvis_security_lockdown_active {metrics['lockdown_active']}",
            "# HELP jarvis_security_offline_mode_active Current offline-mode state.",
            "# TYPE jarvis_security_offline_mode_active gauge",
            f"jarvis_security_offline_mode_active {metrics['offline_mode_active']}",
            "# HELP jarvis_security_audit_log_integrity_valid Audit log hash-chain validation state.",
            "# TYPE jarvis_security_audit_log_integrity_valid gauge",
            f"jarvis_security_audit_log_integrity_valid {metrics['audit_log_integrity_valid']}",
        ]
        return "\n".join(lines) + "\n"

    def list_users(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT username, role, department, is_active, created_at FROM security_users ORDER BY username ASC").fetchall()
        return [dict(row) | {"is_active": bool(row["is_active"])} for row in rows]

    def list_events(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM security_events ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) | {"payload": json.loads(row["payload_json"])} for row in rows]

    def replay_event(self, event_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM security_events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            raise ValueError("Security event not found.")
        return dict(row) | {"payload": json.loads(row["payload_json"])}

    def verify_audit_log_integrity(self) -> dict[str, Any]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, category, severity, actor, message, payload_json, previous_hash, event_hash, created_at FROM security_events ORDER BY created_at ASC"
            ).fetchall()
        previous_hash = ""
        invalid = []
        for row in rows:
            payload_json = row["payload_json"]
            expected = self._hash_event_payload(
                row["id"],
                row["category"],
                row["severity"],
                row["actor"],
                row["message"],
                payload_json,
                row["created_at"],
                previous_hash,
            )
            stored_previous = row["previous_hash"] or ""
            stored_hash = row["event_hash"] or ""
            if stored_previous != previous_hash or stored_hash != expected:
                invalid.append({"event_id": row["id"], "expected_previous_hash": previous_hash, "stored_previous_hash": stored_previous})
            previous_hash = stored_hash or expected
        return {"valid": not invalid, "event_count": len(rows), "invalid_events": invalid[:25]}

    def record_event(self, category: str, severity: str, actor: str, message: str, payload: dict[str, Any]) -> dict[str, Any]:
        payload_json = json.dumps(payload, sort_keys=True)
        previous_hash = self._latest_event_hash()
        event = {
            "id": str(uuid.uuid4()),
            "category": category,
            "severity": severity,
            "actor": actor,
            "message": message,
            "payload_json": payload_json,
            "previous_hash": previous_hash,
            "event_hash": self._hash_event_payload(
                event_id="pending",
                category=category,
                severity=severity,
                actor=actor,
                message=message,
                payload_json=payload_json,
                created_at="pending",
                previous_hash=previous_hash,
            ),
            "created_at": self._now(),
        }
        event["event_hash"] = self._hash_event_payload(
            event_id=event["id"],
            category=category,
            severity=severity,
            actor=actor,
            message=message,
            payload_json=payload_json,
            created_at=event["created_at"],
            previous_hash=previous_hash,
        )
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO security_events (id, category, severity, actor, message, payload_json, previous_hash, event_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tuple(event.values()),
            )
        logger.log("INFO", f"security.{category}", message, payload)
        return event

    def inspect_text(self, text: str) -> list[dict[str, Any]]:
        findings = []
        patterns = {
            "xss": r"<script|javascript:",
            "sql_injection": r"\bunion\b|\bdrop table\b|--|/\*",
            "secret_leak": r"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}",
            "csrf_bypass": r"\bcors\b.*\*",
        }
        lowered = text.lower()
        for label, pattern in patterns.items():
            if re.search(pattern, lowered):
                findings.append({"type": label, "severity": "HIGH", "match": pattern})
        return findings

    def _scan_secrets(self) -> list[dict[str, Any]]:
        findings = []
        for path in self._iter_scannable_files():
            if path.suffix in {".png", ".jpg", ".jpeg", ".ico", ".woff2"}:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                continue
            for issue in self.inspect_text(content):
                findings.append({"path": str(path.relative_to(ROOT_DIR)), **issue})
        return findings[:80]

    def _scan_dependencies(self) -> list[dict[str, Any]]:
        findings = []
        package_lock = ROOT_DIR / "apps" / "desktop" / "package-lock.json"
        if package_lock.exists():
            content = package_lock.read_text(encoding="utf-8")
            if "\"moderate\"" in content:
                findings.append({"path": "apps/desktop/package-lock.json", "type": "dependency_vulnerability", "severity": "MEDIUM", "match": "moderate"})
        return findings

    def _scan_repository(self) -> list[dict[str, Any]]:
        findings = []
        git_dir = ROOT_DIR / ".git"
        if git_dir.exists():
            findings.append({"path": ".git", "type": "repository_scan", "severity": "LOW", "match": "git metadata accessible in workspace"})
        return findings

    def _scan_shell_risks(self) -> list[dict[str, Any]]:
        findings = []
        dangerous = ["reset --hard", "rm -rf", "curl | sh"]
        for path in self._iter_scannable_files(suffixes={".sh"}):
            try:
                content = path.read_text(encoding="utf-8").lower()
            except Exception:
                continue
            for term in dangerous:
                if term in content:
                    findings.append({"path": str(path.relative_to(ROOT_DIR)), "type": "shell_risk", "severity": "HIGH", "match": term})
        return findings

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 160_000).hex()
        return f"{salt}${digest}"

    def _add_backup_tree(self, archive: tarfile.TarFile, source: Path, arcname: str) -> None:
        for path in source.rglob("*"):
            if any(part == "backups" for part in path.parts):
                continue
            if path.is_file():
                archive.add(path, arcname=f"{arcname}/{path.relative_to(source)}")

    def _add_backup_file(self, archive: tarfile.TarFile, source: Path, arcname: str) -> None:
        if source.exists():
            archive.add(source, arcname=arcname)

    def _iter_scannable_files(self, suffixes: set[str] | None = None):
        ignored_dirs = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build", "target", "backups", "logs"}
        seen = 0
        for path in ROOT_DIR.rglob("*"):
            if any(part in ignored_dirs for part in path.parts):
                continue
            if not path.is_file():
                continue
            if suffixes and path.suffix not in suffixes:
                continue
            seen += 1
            if seen > 5000:
                break
            yield path

    def _migrate_event_hashes(self) -> None:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, category, severity, actor, message, payload_json, previous_hash, event_hash, created_at FROM security_events ORDER BY created_at ASC"
            ).fetchall()
            previous_hash = ""
            for row in rows:
                stored_previous = row["previous_hash"] or ""
                stored_hash = row["event_hash"] or ""
                expected_hash = self._hash_event_payload(
                    event_id=row["id"],
                    category=row["category"],
                    severity=row["severity"],
                    actor=row["actor"],
                    message=row["message"],
                    payload_json=row["payload_json"],
                    created_at=row["created_at"],
                    previous_hash=previous_hash,
                )
                if stored_previous != previous_hash or stored_hash != expected_hash:
                    connection.execute(
                        "UPDATE security_events SET previous_hash = ?, event_hash = ? WHERE id = ?",
                        (previous_hash, expected_hash, row["id"]),
                    )
                previous_hash = expected_hash

    def _verify_password(self, password: str, stored: str) -> bool:
        salt, digest = stored.split("$", 1)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 160_000).hex()
        return secrets.compare_digest(candidate, digest)

    def _hash_string(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _hash_event_payload(
        self,
        event_id: str,
        category: str,
        severity: str,
        actor: str,
        message: str,
        payload_json: str,
        created_at: str,
        previous_hash: str,
    ) -> str:
        return hashlib.sha256(
            "|".join([event_id, category, severity, actor, message, payload_json, created_at, previous_hash]).encode("utf-8")
        ).hexdigest()

    def _latest_event_hash(self) -> str:
        with self._connect() as connection:
            row = connection.execute("SELECT event_hash FROM security_events ORDER BY created_at DESC LIMIT 1").fetchone()
        return row["event_hash"] if row and row["event_hash"] else ""

    def _totp_secret(self) -> str:
        return secrets.token_hex(10)

    def _verify_totp(self, secret: str, code: str) -> bool:
        current_bucket = int(datetime.now(UTC).timestamp() // 30)
        expected = hashlib.sha1(f"{secret}:{current_bucket}".encode("utf-8")).hexdigest()[:6]
        return secrets.compare_digest(expected, code)

    def _row_to_user(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "username": row["username"],
            "password_hash": row["password_hash"],
            "role": row["role"],
            "department": row["department"],
            "is_active": bool(row["is_active"]),
            "mfa_secret": row["mfa_secret"],
            "attributes": json.loads(row["attributes_json"]),
        }

    def _epoch(self) -> int:
        return int(datetime.now(UTC).timestamp())

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()


security_engine = SecurityEngine(settings.DATABASE_PATH)
