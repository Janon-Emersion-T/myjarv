# Setup

## Python Brain

```bash
cd /var/www/jarvis
apps/brain/venv/bin/python -m uvicorn app.main:app --app-dir apps/brain --reload
```

## Environment

Copy the example configuration:

```bash
cp .env.example .env.local
```

Important current settings:

* `DATABASE_BACKEND=sqlite`
* `DATABASE_PATH=/var/www/jarvis/data/jarvis.sqlite3`
* `POSTGRES_DSN=...` for future PostgreSQL wiring
* `LOCAL_AUTH_TOKEN=...` to enable header-based local auth
* `PRODUCTION_LOCK_MODE=false`

## Validation

```bash
python3 scripts/validate_agents.py
python3 scripts/audit_agent_profiles.py | tail -20
```

## Desktop App

```bash
cd /var/www/jarvis/apps/desktop
npm install
npm run build
```

## Rust Core

```bash
cd /var/www/jarvis/apps/rust-core
cargo check
```

