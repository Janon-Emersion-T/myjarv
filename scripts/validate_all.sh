#!/usr/bin/env bash
set -e

python3 scripts/check_architecture.py
python3 scripts/validate_agents.py
python3 scripts/audit_agent_profiles.py | tail -20

cd apps/rust-core
cargo check

cd ../desktop
npm run build

cd ../../
apps/brain/venv/bin/python -m pytest apps/brain/tests
