# Approval System

Approval levels:

* `LOW`
* `MEDIUM`
* `HIGH`
* `CRITICAL`

Task approval records are persisted in SQLite and returned through task detail payloads.

Current behavior:

* low-risk work can remain planned
* medium, high, and critical work moves to `pending_approval`
* approval and rejection are persisted with reviewer and notes

