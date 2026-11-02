"""Shared helpers for Expense Receipt Processor Claude Code hooks.

Cross-platform (Windows/macOS/Linux) — stdlib only, no third-party deps.
"""

import datetime
import json
import os
import sys

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
CLAUDE_DIR = os.path.dirname(HOOKS_DIR)
LOG_PATH = os.path.join(CLAUDE_DIR, "logs", "hooks.log")


def read_hook_input():
    """Read and parse the hook JSON payload from stdin. Returns {} on empty/invalid input."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def log(event, decision, reason, extra=None):
    """Append one line to .claude/logs/hooks.log."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    line = f"[{timestamp}] event={event} decision={decision} reason={reason}"
    if extra:
        line += f" extra={extra}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def block(event, reason, extra=None):
    """Log the block, print the reason to stderr, and exit 2 (blocks the tool call)."""
    log(event, "blocked", reason, extra)
    sys.stderr.write(f"BLOCKED: {reason}\n")
    sys.exit(2)


def allow(event, reason="no rule matched", extra=None, quiet=True):
    """Allow the tool call to proceed. Only logs when quiet=False, to keep the log focused on blocks/runs."""
    if not quiet:
        log(event, "allowed", reason, extra)
    sys.exit(0)
