# Security

## Current Security Foundations

* approval classification with explicit levels
* persistent approval history
* persistent audit-style JSONL logs
* local auth placeholder through `X-Jarvis-Token`
* production lock mode flag
* registry-level authority and risk metadata

## Current Gaps

* no full user account system yet
* no secret vault yet
* no encryption-at-rest yet
* no full RBAC matrix yet

## Dangerous Actions

These actions are treated as high-risk or critical:

* delete or destructive file actions
* deploy operations
* git push
* email or WhatsApp sending
* finance or legal modifications
* shell command execution
* secret or credential use

