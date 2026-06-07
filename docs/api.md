# API

Base service: `apps/brain/app/main.py`

## Endpoints

* `GET /health`
* `GET /agents`
* `GET /agents/{name}`
* `POST /tasks`
* `GET /tasks`
* `GET /tasks/{id}`
* `POST /tasks/{id}/approve`
* `POST /tasks/{id}/reject`
* `GET /tasks/{id}/approvals/policy`
* `POST /tasks/{id}/approvals/simulate`
* `POST /tasks/{id}/approvals/{approval_id}/revoke`
* `POST /tasks/{id}/approvals/rollback`
* `GET /approvals/queue`
* `GET /approvals/history`
* `GET /approvals/metrics`
* `GET /approvals/quarantine`
* `GET /approvals/archive`
* `GET /approvals/channels`
* `GET /approvals/emergency-shutdown`
* `POST /approvals/emergency-shutdown`
* `GET /memory`
* `POST /memory`
* `GET /logs`
* `GET /knowledge`
* `GET /knowledge/search`
* `GET /knowledge/analytics`
* `GET /knowledge/validate`
* `GET /knowledge/sources`
* `GET /knowledge/quarantine`
* `GET /knowledge/graph`
* `GET /knowledge/gaps`
* `GET /knowledge/pipelines`
* `POST /knowledge/reindex`
* `GET /tools`
* `GET /tools/{name}`
* `GET /tools/capabilities`
* `GET /tools/compatibility`
* `GET /tools/adapters`
* `GET /tools/validate`
* `GET /tools/history`
* `GET /tools/analytics`
* `GET /tools/health`
* `GET /tools/metrics`
* `POST /tools/execute`
* `POST /tools/workflows`
* `POST /tools/queue/process`
* `POST /tools/replay/{execution_id}`
* `GET /developer/scan`
* `GET /developer/health`
* `GET /developer/errors`
* `GET /developer/analytics`
* `GET /developer/deployment-checklist`
* `POST /developer/fix-plan`
* `POST /developer/changelog`
* `GET /business/analytics`
* `GET /business/leads`
* `POST /business/leads`
* `POST /business/leads/{lead_id}/qualify`
* `GET /business/proposals`
* `POST /business/proposals`
* `POST /business/quotations`
* `POST /business/followups`
* `POST /business/invoices/reminders`
* `POST /business/onboarding`
* `POST /business/competitors/analyze`
* `POST /business/blog-drafts`
* `POST /business/reports/monthly`
* `GET /projects`
* `POST /projects`
* `GET /projects/{project_id}`
* `GET /projects/analytics`
* `POST /projects/{project_id}/milestones`
* `POST /projects/{project_id}/blockers`
* `POST /projects/{project_id}/dependencies`
* `POST /projects/{project_id}/worklogs`
* `POST /projects/{project_id}/reports/{report_type}`
* `GET /settings`
* `GET /browser/plan`
* `GET /workflows/business`
* `GET /workflows/developer`
* `GET /dashboard/developer`
* `GET /dashboard/business`
* `GET /dashboard/projects`
* `WS /ws/approvals`

## Auth Placeholder

If `LOCAL_AUTH_TOKEN` or `PRODUCTION_LOCK_MODE` is enabled, send:

```http
X-Jarvis-Token: <token>
```
