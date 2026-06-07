# Project Manager Mode

Roadmap Phase 11 now includes a real project-management layer instead of task-pipeline placeholders.

## Current Capabilities

* project creation with client, category, methodology, owner, deadline, and budget
* automatic phase templates for agile, scrum, kanban, and waterfall projects
* task decomposition and agent assignment hints
* milestones, blockers, dependencies, and worklogs
* deadline-risk and health/risk scoring
* budget and invoice status tracking
* sprint, kanban, burndown, and timeline views
* daily, weekly, client, and invoice report generation
* project memory integration
* knowledge-backed playbook suggestions
* dashboard, API, CLI, and desktop projects-view support

## Main Endpoints

* `GET /projects`
* `POST /projects`
* `GET /projects/{project_id}`
* `GET /projects/analytics`
* `POST /projects/{project_id}/milestones`
* `POST /projects/{project_id}/blockers`
* `POST /projects/{project_id}/dependencies`
* `POST /projects/{project_id}/worklogs`
* `POST /projects/{project_id}/reports/daily`
* `POST /projects/{project_id}/reports/weekly`
* `POST /projects/{project_id}/reports/client`
* `POST /projects/{project_id}/reports/invoice`
* `GET /dashboard/projects`

## CLI

* `python3 scripts/project_cli.py list`
* `python3 scripts/project_cli.py analytics`
* `python3 scripts/project_cli.py dashboard --compact`
* `python3 scripts/test_projects.py`

## Notes

Project runtime records are stored under `data/projects/` and treated as local operational state.
