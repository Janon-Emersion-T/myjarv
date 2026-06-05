# Routing Engine

This module owns Jarvis task routing for LKProfessionals.

## Responsibilities

* classify task intent
* score candidate agents
* detect ambiguity and duplicates
* build sequential or parallel execution plans
* assign reviewers and escalation chains
* persist route traces for replay and analytics
* support simulation mode and manual reassignment

## Main Files

* `engine.py` builds route decisions
* `rules.py` loads the JSON routing rules
* `store.py` persists traces and analytics in SQLite

## Runtime Inputs

* task message
* requested action
* preferred agent
* metadata such as client, project, memory scopes, blacklist, whitelist, retry state

## Outputs

* selected primary agent
* collaborators
* review chain
* escalation chain
* execution strategy
* confidence score
* subtasks and stages
* persisted trace id
