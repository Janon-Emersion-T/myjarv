from pathlib import Path

from app.config import ROOT_DIR


PERSONALITY_PATH = ROOT_DIR / "packages" / "prompts" / "jarvis-personality.md"


def load_jarvis_personality() -> str:
    return PERSONALITY_PATH.read_text(encoding="utf-8")


def apply_personality(base_prompt: str) -> str:
    personality = load_jarvis_personality()
    return f"{personality}\n\n{base_prompt}".strip()

