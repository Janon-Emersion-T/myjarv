# Approval System

Phase 10 is now implemented as a durable approval subsystem rather than a simple yes/no gate.

## Core Behavior

* `LOW` tasks can execute without approval.
* `MEDIUM` tasks require a manager-stage approval.
* `HIGH` tasks require a manager plus director chain.
* `CRITICAL` tasks require manager, director, and executive approvals plus written signoff.

## Policy Engine

The approval engine now builds task-specific policy from:

* approval level
* risk level
* message and requested action keywords
* department context carried in task metadata

Supported contextual rule domains include:

* finance
* deployment / production
* filesystem
* communication
* legal
* shell access
* browser automation
* autonomous AI actions

## Recorded Approval Data

Each approval record now stores:

* reviewer, notes, role, department, delegation source
* channel: `dashboard`, `api`, `cli`, `mobile`, `email`, `whatsapp`, or `voice`
* approval token and replay hash
* confidence score
* suspicious flags
* stage and chain position
* signed immutable hash
* written document and evidence attachments
* revocation metadata

SQLite tables now include:

* `approvals`
* `approval_events`
* `approval_artifacts`
* `approval_controls`

Approval artifacts are also written to `data/approvals/<task_id>/<approval_id>.json`.

## Safety Controls

The system now supports:

* human-in-the-loop enforcement
* role-based and department-based approval rules
* duplicate and replay detection
* suspicious / fraud-style flagging
* emergency override capture
* emergency shutdown control
* revocation and rollback
* rejected-action quarantine
* blocked-action archive
* simulation before committing an approval

## APIs And Realtime

Approval APIs now include queue, history, metrics, quarantine, archive, policy lookup, simulation, revocation, rollback, and emergency shutdown control.

Realtime approval updates are available through:

* `GET /approvals/*`
* `POST /tasks/{task_id}/approvals/*`
* `POST /approvals/emergency-shutdown`
* `WS /ws/approvals`

## Verification

Primary verification lives in:

* `apps/brain/tests/test_phase10_approvals.py`
* `scripts/approval_cli.py`
* `scripts/test_approvals.py`
