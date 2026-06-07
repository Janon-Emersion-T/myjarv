# Developer Mode

Roadmap Phase 12 now has a live local-first developer service instead of static workflow notes.

## Current Capabilities

* repository scanning and indexing
* stack, language, and framework detection
* multi-repository discovery inside the workspace
* heuristic error and risk detection
* repository health scoring
* fix-plan generation
* changelog generation
* deployment checklist generation
* dashboard, API, and CLI access

## Main Endpoints

* `GET /developer/scan`
* `GET /developer/health`
* `GET /developer/errors`
* `GET /developer/analytics`
* `GET /developer/deployment-checklist`
* `POST /developer/fix-plan`
* `POST /developer/changelog`

## CLI

* `python3 scripts/developer_cli.py scan`
* `python3 scripts/developer_cli.py health`
* `python3 scripts/developer_cli.py plan "Goal"`
* `python3 scripts/test_developer_mode.py`

## Notes

Developer snapshots are stored under `data/developer/` and treated as runtime artifacts.
