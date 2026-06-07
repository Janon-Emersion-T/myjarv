---
title: Selenium Automation Notes
summary: Selenium usage guidance for environments where Playwright is unavailable or legacy suites remain.
tags: ["selenium", "automation", "browser", "legacy"]
sources: ["internal"]
confidence: 0.76
verified: true
version: 1.0
last_reviewed: 2026-06-07
approval_status: approved
trusted: true
domain: automation
department: development
frameworks: ["selenium"]
languages: ["python", "java"]
---
# Selenium Automation Notes

- Reserve Selenium for legacy coverage or environments that cannot run Playwright cleanly.
- Stabilize waits around observable page conditions instead of fixed sleeps.
- Keep browser-driver versioning pinned in CI documentation to reduce flaky runs.
