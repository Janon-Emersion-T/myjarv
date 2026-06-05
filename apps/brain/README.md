# Jarvis Brain

The Python brain is the orchestration layer for Jarvis.

Current responsibilities:

* agent loading
* task routing
* approval classification
* approval-aware task execution
* result review and quality scoring
* SQLite-backed task and memory records
* task lifecycle history persistence
* knowledge retrieval
* tool registry exposure
* API endpoints for desktop and future worker clients

Phase 4 status:

* wrapper modules now exist directly under `apps/brain/` for roadmap-level compatibility
* the execution lifecycle supports `received -> routed -> waiting_approval/approved -> executing -> completed/failed`
* tests for routing, approval, memory, and task flow live in `apps/brain/tests/test_phase4.py`

SQLite is the default local-first backend. PostgreSQL can be reintroduced later through the configured `POSTGRES_DSN` path without breaking the higher-level module boundaries.
