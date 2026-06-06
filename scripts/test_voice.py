#!/usr/bin/env python3
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.voice.engine import voice_engine  # noqa: E402


def main() -> int:
    session = voice_engine.create_session(mode="desktop_assistant", locale="en", speaker_id="janon", text="Hey Jarvis")
    result = voice_engine.handle_command(
        session["id"],
        text="Jarvis open the latest approvals",
        requested_action="open approvals",
        locale="en",
        speaker_id="janon",
        confidence=None,
        metadata={"cli_test": True},
    )
    print(
        json.dumps(
            {
                "session_id": session["id"],
                "status": result["session"]["status"],
                "intent": result["interaction"]["intent"],
                "confidence": result["interaction"]["confidence"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
