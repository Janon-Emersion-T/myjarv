#!/usr/bin/env python3
import argparse
import json
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.orchestrator import orchestrate_task  # noqa: E402
from app.schemas import TaskCreateRequest  # noqa: E402
from app.task_manager import task_manager  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Jarvis multi-agent collaboration.")
    parser.add_argument("message", help="Task message to collaborate on.")
    parser.add_argument("--requested-action", dest="requested_action")
    parser.add_argument("--preferred-agent", dest="preferred_agent")
    parser.add_argument("--metadata", default="{}", help="JSON metadata context.")
    args = parser.parse_args()

    metadata = json.loads(args.metadata)
    request = TaskCreateRequest(
        message=args.message,
        requested_action=args.requested_action,
        preferred_agent=args.preferred_agent,
        metadata={"cli_test": True, "run_id": uuid.uuid4().hex[:8], **metadata},
    )
    task = task_manager.create_task(orchestrate_task(request))
    if task["approval_level"] != "LOW":
        task = task_manager.approve_task(task["id"], "CLI", "Automated CLI collaboration test approval.")
    executed = task_manager.execute_task(task["id"], executor="CLI", force_retry=False)
    payload = {
        "task_id": executed["id"],
        "status": executed["status"],
        "selected_agent": executed["selected_agent"]["name"],
        "collaboration_session_id": executed["execution_result"]["collaboration_session_id"],
        "contribution_count": executed["execution_result"]["contribution_count"],
        "review_chain_results": executed["execution_result"]["review_chain_results"],
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
