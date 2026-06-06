#!/usr/bin/env python3
import json
import statistics
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.voice.engine import voice_engine  # noqa: E402


def run_once(index: int) -> float:
    started = time.perf_counter()
    session = voice_engine.create_session(mode="command", locale="en", speaker_id="janon", text=f"Jarvis run {index}")
    voice_engine.handle_command(
        session["id"],
        text=f"Jarvis status report benchmark {index}",
        requested_action="status",
        locale="en",
        speaker_id="janon",
        confidence=None,
        metadata={"benchmark": True},
    )
    return (time.perf_counter() - started) * 1000


def main() -> int:
    samples = [run_once(index) for index in range(8)]
    print(
        json.dumps(
            {
                "runs": len(samples),
                "min_ms": round(min(samples), 2),
                "max_ms": round(max(samples), 2),
                "avg_ms": round(statistics.mean(samples), 2),
                "median_ms": round(statistics.median(samples), 2),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
