# Workflow Replacement

Roadmap Phase 14 now includes a durable workflow-replacement layer for staff-facing operational roles.

## Covered Replacement Packs

* receptionist
* sales assistant
* project coordinator
* junior developer
* SEO assistant
* content writer
* finance assistant
* support assistant
* documentation assistant
* QA tester

## Current Capabilities

* workflow replacement architecture and reusable role catalog
* workflow decomposition, dependency mapping, and timeline analysis
* automation, risk, confidence, and approval-confidence scoring
* approval policy mapping and human-review checkpoints
* simulation, replay, rollback-readiness, and failure-recovery guidance
* tool, memory, knowledge, and browser-plan integration
* SOP and documentation generation
* bottleneck, KPI, and analytics reporting
* dashboard, API, and CLI access

## Main Endpoints

* `GET /workflows/replacements`
* `GET /workflows/replacements/catalog`
* `POST /workflows/replacements`
* `GET /workflows/replacements/{workflow_id}`
* `GET /workflows/replacements/analytics`
* `POST /workflows/replacements/{workflow_id}/simulate`
* `POST /workflows/replacements/{workflow_id}/replay`
* `GET /dashboard/workflows`

## CLI

* `python3 scripts/workflow_cli.py catalog`
* `python3 scripts/workflow_cli.py analytics`
* `python3 scripts/workflow_cli.py dashboard`
* `python3 scripts/test_workflows.py`

## Notes

Workflow runtime records are stored under `data/workflows/` and treated as local operational state.
