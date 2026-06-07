---
title: PostgreSQL Migration Notes
summary: Guidance for moving local-first SQLite workloads into PostgreSQL without breaking higher-level interfaces.
tags: ["postgresql", "database", "migration", "sql"]
sources: ["postgresql", "internal"]
confidence: 0.89
verified: true
version: 1.0
last_reviewed: 2026-06-07
approval_status: approved
trusted: true
domain: backend
department: development
frameworks: ["sqlalchemy"]
languages: ["sql"]
---
# PostgreSQL Migration Notes

- Keep repository and store APIs backend-neutral before introducing PostgreSQL.
- Normalize timestamps to UTC and document any JSON column assumptions early.
- Plan indexes around read paths, replay queries, and time-ordered dashboards.
- Use migrations for schema evolution rather than runtime auto-creation in production.
- Verify backup, restore, and connection pooling behavior before promoting PostgreSQL to default.
