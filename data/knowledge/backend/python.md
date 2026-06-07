---
title: Python Service Conventions
summary: Python service guidelines for local-first APIs, background workflows, and maintainable business logic.
tags: ["python", "backend", "api", "testing"]
sources: ["python", "internal"]
confidence: 0.93
verified: true
version: 1.0
last_reviewed: 2026-06-07
approval_status: approved
trusted: true
domain: backend
department: development
frameworks: ["fastapi"]
languages: ["python"]
---
# Python Service Conventions

- Keep request validation, orchestration, and persistence responsibilities separated.
- Prefer deterministic pure functions around business rules so unit tests stay fast and focused.
- Use typed models for API boundaries and normalize data as close to ingestion as possible.
- Store operational events in structured logs with identifiers that support replay and audits.
- Avoid hidden global state except for explicit singleton services such as stores and registries.
