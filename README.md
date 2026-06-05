# Jarvis for LKProfessionals

Jarvis is a local-first company operating platform for LKProfessionals (Pvt) Ltd.

It is designed as a multi-agent system with:

* a Python FastAPI orchestration brain
* a SQLite-first local data layer
* a future-compatible PostgreSQL path
* a Tauri + React + Tailwind desktop frontend
* a Rust utility workspace for guardrails and system-facing services

## Current State

Completed foundations:

* audited repository and phase tracker
* standardized agent profiles
* enriched agent registry with authority and risk metadata
* Python brain with tasks, approvals, memory, logs, knowledge, and tools endpoints
* knowledge base folders and loader
* tool registry
* Rust core workspace
* desktop frontend skeleton
* voice, vision, and browser-planning interfaces
* business and developer workflow templates
* local auth placeholder and production lock mode

## Main Directories

* [apps/brain](/var/www/jarvis/apps/brain/README.md)
* [apps/desktop](/var/www/jarvis/apps/desktop/package.json)
* [apps/rust-core](/var/www/jarvis/apps/rust-core/README.md)
* [packages/agents](/var/www/jarvis/packages/agents/registry.json)
* [packages/tools](/var/www/jarvis/packages/tools/registry.json)
* [data/knowledge](/var/www/jarvis/data/knowledge)
* [docs](/var/www/jarvis/docs/phase-status.md)

## Quick Start

Python brain:

```bash
cd /var/www/jarvis
apps/brain/venv/bin/python -m uvicorn app.main:app --app-dir apps/brain --reload
```

Validation:

```bash
python3 scripts/validate_agents.py
python3 scripts/audit_agent_profiles.py | tail -20
```

Rust workspace:

```bash
cd /var/www/jarvis/apps/rust-core
cargo check
```

Desktop app:

```bash
cd /var/www/jarvis/apps/desktop
npm install
npm run build
```

## Key Docs

* [docs/architecture.md](/var/www/jarvis/docs/architecture.md)
* [docs/setup.md](/var/www/jarvis/docs/setup.md)
* [docs/api.md](/var/www/jarvis/docs/api.md)
* [docs/frontend.md](/var/www/jarvis/docs/frontend.md)
* [docs/rust-core.md](/var/www/jarvis/docs/rust-core.md)
* [docs/security.md](/var/www/jarvis/docs/security.md)
* [docs/phase-status.md](/var/www/jarvis/docs/phase-status.md)

