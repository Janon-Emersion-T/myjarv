# Architecture Scorecard

| Area | Target | Current | Status |
|---|---:|---:|---|
| Module boundaries | 10 | 8 | Needs boundary rules |
| Security model | 10 | 6 | Defaults need hardening |
| Data ownership | 10 | 7 | Needs ownership map |
| Event contracts | 10 | 6 | Needs standard event schema |
| Tool architecture | 10 | 8 | Strong, needs stricter gates |
| Desktop separation | 10 | 8 | Good |
| Rust integration | 10 | 6 | Needs clearer role |
| Production readiness | 10 | 4 | Needs gates |
| Observability | 10 | 7 | Needs unified event bus |
| Extension governance | 10 | 5 | Needs rules |

## Architecture is 10/10 only when:
- every module has an owner;
- every dangerous action requires approval;
- every tool has risk metadata;
- every event follows one schema;
- production cannot start with default credentials;
- backup and restore are tested;
- API, desktop, and Rust checks pass.