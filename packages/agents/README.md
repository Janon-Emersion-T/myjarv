# Agent Registry

This directory contains the live Jarvis agent registry, company structure data, prompt files, and profile templates.

Source-of-truth files:

* `registry.json` — runtime agent registry for the brain
* `company-structure.json` — organizational model used to enrich registry metadata
* `schema.json` — compatibility schema path referenced by the roadmap
* `prompts/*.md` — canonical agent profiles with preserved legacy prompt bodies

Validation and generation commands:

```bash
python3 scripts/generate_agent_registry.py
python3 scripts/validate_agents.py
python3 scripts/agent_registry_cli.py list
python3 scripts/agent_registry_cli.py show jarvis
python3 scripts/agent_registry_cli.py validate
```

Registry guarantees:

* every agent maps to a real company role
* every prompt file referenced by the registry must exist
* orphan prompt files are detected
* duplicate names and duplicate roles are detected
* department grouping is exposed for the API and desktop app
