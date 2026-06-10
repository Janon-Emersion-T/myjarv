from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "docs/architecture.md",
    "docs/architecture-scorecard.md",
    "docs/module-boundaries.md",
    "docs/runtime-topology.md",
    "docs/production-gates.md",
    "docs/event-contracts.md",
    "docs/data-ownership.md",
]

REQUIRED_DIRS = [
    "apps/brain/app",
    "apps/desktop",
    "apps/rust-core",
    "packages/agents",
    "packages/tools",
    "data/knowledge",
]

REQUIRED_ARCH_SECTIONS = [
    "Architecture Target",
    "Non-Negotiable Principles",
    "System Context",
    "Runtime Layers",
    "Approval and Risk Layer",
    "Security Layer",
    "Event and Observability Layer",
    "Production Architecture Gates",
    "Extension Rules",
]

errors = []

for path in REQUIRED_DOCS:
    if not (ROOT / path).exists():
        errors.append(f"Missing required doc: {path}")

for path in REQUIRED_DIRS:
    if not (ROOT / path).exists():
        errors.append(f"Missing required directory: {path}")

architecture_file = ROOT / "docs/architecture.md"
if architecture_file.exists():
    content = architecture_file.read_text(encoding="utf-8")
    for section in REQUIRED_ARCH_SECTIONS:
        if section not in content:
            errors.append(f"Missing architecture section: {section}")

config_file = ROOT / "apps/brain/app/config.py"
if config_file.exists():
    config = config_file.read_text(encoding="utf-8")
    forbidden = [
        'SECURITY_BOOTSTRAP_PASSWORD: str = "change-me-now"',
        "SECURITY_REQUIRE_AUTH: bool = False",
    ]
    for item in forbidden:
        if item in config:
            errors.append(f"Unsafe config default found: {item}")

if errors:
    print("Architecture check failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Architecture check passed.")
