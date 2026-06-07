---
title: Prometheus Monitoring Notes
summary: Metrics collection guidance for service health, alerting signals, and capacity planning.
tags: ["prometheus", "metrics", "monitoring", "ops"]
sources: ["internal"]
confidence: 0.82
verified: true
version: 1.0
last_reviewed: 2026-06-07
approval_status: approved
trusted: true
domain: devops
department: infrastructure
frameworks: ["prometheus"]
languages: ["metrics"]
---
# Prometheus Monitoring Notes

- Instrument counters, gauges, and histograms around actual operator decisions.
- Avoid high-cardinality labels that make dashboards and storage expensive.
- Pair alerts with actionable runbook links whenever possible.
