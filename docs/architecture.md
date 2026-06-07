# Architecture

## Core Principles

* Python is the main AI brain and orchestration layer.
* Rust is used for performance-sensitive and system-facing utilities.
* Tauri + React + Tailwind provide the desktop experience.
* SQLite is the default local-first persistence layer.
* PostgreSQL remains a future-compatible option through configuration, not a required runtime dependency.

## Current Layers

### Brain

Located in `apps/brain/app`.

Main responsibilities:

* load agents from the registry
* classify tasks by intent, priority, risk, and approval requirement
* enforce staged approval policy, revocation, rollback, quarantine, and emergency shutdown controls
* persist tasks, approvals, approval events, approval artifacts, and memory
* expose API endpoints to the desktop app and future workers
* retrieve knowledge and tool definitions

### Registry

Located in `packages/agents/registry.json`.

The registry stores:

* department
* role
* model role
* profile path
* priority
* risk level
* approval level
* tools
* authority scope

### Memory

SQLite-backed tables currently store:

* tasks
* approvals
* approval events
* approval artifacts
* memory entries

Memory scopes:

* company
* client
* project
* decision
* mistake
* agent
* user preference

### Approval Layer

The approval subsystem now includes a dedicated policy engine, request tracking, confidence scoring, signed approval records, replay protection, multi-stage chains, emergency controls, websocket event streaming, and CLI verification. Approval evidence is persisted in SQLite plus sidecar JSON artifacts under `data/approvals`.

### Knowledge

Structured knowledge now lives in `data/knowledge` across markdown and JSON sources, with metadata-aware indexing, semantic-style retrieval, validation, source tracking, relationship graphing, and API/CLI inspection support.

### Tools

Tool definitions live in `packages/tools/registry.json` and are validated against `packages/tools/schema.json`. The Python brain now exposes registry discovery, approval-aware execution, queued workflows, replayable history, compatibility mapping, metrics, and adapter descriptors through the tool API.

### Desktop

The desktop app lives in `apps/desktop` and is configured for Tauri + React + Tailwind.

### Rust Core

The Rust workspace lives in `apps/rust-core` and currently exposes small CLI-oriented crates for future Python integration.
