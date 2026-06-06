# Collaboration Engine

This module runs multi-agent collaboration for Jarvis task execution.

## What It Handles

* session planning for primary agents, collaborators, and reviewers
* agent-to-agent instructions, handoffs, reviews, and escalation messages
* event bus publishing for messages, contributions, and timeline events
* shared workspace assembly from memory, knowledge, and routing context
* sequential and parallel collaboration execution
* contribution tracking, quality scoring, and replayable session history
* collaboration analytics and websocket-ready event streaming

## Main Files

* `engine.py` creates and executes collaboration sessions
* `protocol.py` defines message patterns between agents
* `bus.py` provides in-process event distribution
* `store.py` persists sessions, messages, events, and contributions
