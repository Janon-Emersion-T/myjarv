# Jarvis Brain

The Python brain is the orchestration layer for Jarvis.

Current responsibilities:

* agent loading
* task routing
* approval classification
* SQLite-backed task and memory records
* knowledge retrieval
* tool registry exposure
* API endpoints for desktop and future worker clients

SQLite is the default local-first backend. PostgreSQL can be reintroduced later through the configured `POSTGRES_DSN` path without breaking the higher-level module boundaries.

