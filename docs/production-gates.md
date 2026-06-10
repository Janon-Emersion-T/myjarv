# Production Gates

Jarvis is production-ready only when:

## Security
- Auth enabled
- Default password removed
- Strong secret key configured
- Production lock mode enabled
- Audit integrity passes

## Data
- SQLite backup works
- Restore test works
- PostgreSQL migration path documented

## Tools
- Dangerous tools require approval
- Tool history works
- Replay works

## Runtime
- FastAPI starts
- Desktop builds
- Rust cargo check passes
- Tests pass

## Operations
- Emergency shutdown works
- Offline mode works
- Daily CEO report works