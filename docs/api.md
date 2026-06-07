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
* `GET /settings`
* `GET /browser/plan`
* `GET /workflows/business`
* `GET /workflows/developer`

## Auth Placeholder

If `LOCAL_AUTH_TOKEN` or `PRODUCTION_LOCK_MODE` is enabled, send:

```http
X-Jarvis-Token: <token>
```
