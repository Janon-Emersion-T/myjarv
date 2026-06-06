# Security

## Current Security Foundations

* multi-user authentication with signed bearer sessions
* optional local token fallback through `X-Jarvis-Token`
* role-based and attribute-aware authorization checks
* API key management with scoped roles
* encrypted local secret vault
* encrypted backup and recovery workflows
* audit-style JSONL logs plus replayable security event history
* rate limiting and request inspection for suspicious input
* emergency lockdown mode and secure offline mode
* security scans, incidents, compliance reporting, and metrics
* agent-level permission inspection against risk and approval metadata

## Main Endpoints

* `POST /auth/login`
* `POST /auth/logout`
* `POST /auth/mfa/verify`
* `GET /auth/me`
* `GET /security/dashboard`
* `GET /security/events`
* `GET /security/audit-integrity`
* `GET /security/metrics`
* `GET /security/vault/providers`
* `POST /security/api-keys`
* `POST /security/secrets`
* `POST /security/backups`
* `POST /security/backups/{backup_id}/test-restore`
* `POST /security/scans`
* `POST /security/lockdown`
* `POST /security/unlock`
* `POST /security/offline-mode`

## Dangerous Actions

These actions are treated as high-risk or critical:

* delete or destructive file actions
* deploy operations
* git push
* email or WhatsApp sending
* finance or legal modifications
* shell command execution
* secret or credential use

## Notes

* SQLite remains the active local-first backend, but the security layer is structured so PostgreSQL-backed persistence can be added later.
* HashiCorp Vault and cloud secret manager support are exposed as provider-ready configuration points, without making paid infrastructure mandatory.
