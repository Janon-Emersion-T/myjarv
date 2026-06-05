# Deployment

Current deployment mode is local-first development.

Near-term deployment path:

1. run the Python brain
2. validate the registry and docs
3. build the desktop frontend
4. validate the Rust workspace
5. enable production lock mode before any externally impactful automation

Production deployment should remain approval-gated and should not auto-run from agent output without explicit human approval.

