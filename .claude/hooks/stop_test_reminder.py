#!/usr/bin/env python3
"""Stop hook.

Prints a reminder (via systemMessage) if backend tests (pytest) have not been
run yet in this session, per the marker written by track_test_runs.py.
Cross-platform: stdlib only, reads hook JSON from stdin.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_common import CLAUDE_DIR, log  # noqa: E402

EVENT = "Stop:stop_test_reminder"
MARKERS_DIR = os.path.join(CLAUDE_DIR, "logs", "test-run-markers")


def session_has_run_tests(session_id: str) -> bool:
    """Return True if a test-run marker exists for this session."""
    marker_path = os.path.join(MARKERS_DIR, f"{session_id}.marker")
    return os.path.exists(marker_path)


def main() -> None:
    """Read the Stop payload from stdin and emit a reminder if tests were not run."""
    payload = json.loads(sys.stdin.read() or "{}")
    session_id = payload.get("session_id", "unknown")

    if session_has_run_tests(session_id):
        log(EVENT, "skipped", "backend tests were run this session", extra=session_id)
        sys.exit(0)

    log(EVENT, "reminded", "backend tests not run this session", extra=session_id)
    message = {
        "systemMessage": (
            "Reminder: backend tests (pytest) have not been run yet this "
            "session. Run `pytest` under backend/ before considering the "
            "work done."
        )
    }
    sys.stdout.write(json.dumps(message) + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
