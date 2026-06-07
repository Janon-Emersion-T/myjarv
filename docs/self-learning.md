# Self-Learning

Jarvis now includes a review-gated self-learning engine in `apps/brain/app/self_learning.py`.

## Capabilities

* capture successful and failed task outcomes as learning events
* detect repeated error signals from recent logs
* generate lessons learned and reusable playbook candidates
* stage knowledge updates for human review before apply
* apply approved learning updates into `data/knowledge/company/self-learning`
* version each applied update under `data/learning/versions`
* expose dashboard, analytics, lesson, playbook, and update APIs
* support CLI inspection and scripted validation

## Safety Model

* learning runs are safe by default and never auto-apply knowledge
* each proposed update requires explicit review
* applying an update writes a version snapshot and semantic diff
* knowledge is reindexed after approved application
