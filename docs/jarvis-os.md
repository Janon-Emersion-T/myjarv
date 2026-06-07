# Jarvis OS

Jarvis now exposes a unified operating-system layer in `apps/brain/app/jarvis_os.py`.

## Responsibilities

* aggregate module health for dashboard, memory, knowledge, tools, approvals, projects, developer mode, business automation, workflows, security, voice, and self-learning
* publish a consolidated operating snapshot
* generate daily CEO, weekly strategy, and monthly business reports
* surface domain-assistant coverage across developer, marketing, finance, legal, HR, and client-support lanes
* expose cross-module recommendations and an aggregated event bus

## Interfaces

* `GET /os/dashboard`
* `GET /os/modules`
* `GET /os/assistants`
* `GET /os/recommendations`
* `GET /os/event-bus`
* `GET /os/reports/{report_type}`
