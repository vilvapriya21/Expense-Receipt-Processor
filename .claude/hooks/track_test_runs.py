#!/usr/bin/env python3
"""PostToolUse hook for Bash.

Records, per session, whether a backend test command (pytest) has been run.
The Stop hook (stop_test_reminder.py) reads this marker to decide whether to
remind the user. Cross-platform: stdlib only, reads hook JSON from stdin.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_common import CLAUDE_DIR, log  # noqa: E402

EVENT = "PostToolUse:track_test_runs"
MARKERS_DIR = os.path.join(CLAUDE_DIR, "logs", "test-run-markers")
PYTEST_PATTERN = re.compile(r"\bpytest\b")


def mark_session_tested(session_id: str) -> None:
    """Create a marker file recording that backend tests ran in this session."""
    os.makedirs(MARKERS_DIR, exist_ok=True)
    marker_path = os.path.join(MARKERS_DIR, f"{session_id}.marker")
    with open(marker_path, "w", encoding="utf-8") as f:
        f.write("pytest run detected\n")


def main() -> None:
    """Read the PostToolUse Bash payload from stdin and mark the session if pytest ran."""
    payload = json.loads(sys.stdin.read() or "{}")
    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""
    session_id = payload.get("session_id", "unknown")

    if PYTEST_PATTERN.search(command):
        mark_session_tested(session_id)
        log(EVENT, "marked", "pytest invocation detected", extra=session_id)

    sys.exit(0)


if __name__ == "__main__":
    main()
