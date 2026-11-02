#!/usr/bin/env python3
"""PreToolUse hook for Bash.

Blocks destructive shell commands (recursive deletes of root/home/project,
force-pushes, SQL DROP TABLE, deleting the sqlite db) and secret leaks
(echoing API keys / tokens). Cross-platform: stdlib only, reads hook JSON
from stdin.
"""

import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_common import allow, block  # noqa: E402

EVENT = "PreToolUse:guard_bash"

# Each rule is (compiled regex, human-readable reason). First match wins.
DESTRUCTIVE_RULES = [
    (
        re.compile(
            r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)"
            r"\s+(/|~|\$HOME|\.|\*)(\s|$)"
        ),
        "recursive force-delete targeting root, home, or the current (project) directory",
    ),
    (
        re.compile(r"\bremove-item\b.*-recurse.*-force", re.IGNORECASE),
        "recursive force-delete (Remove-Item -Recurse -Force)",
    ),
    (
        re.compile(r"\bremove-item\b.*-force.*-recurse", re.IGNORECASE),
        "recursive force-delete (Remove-Item -Recurse -Force)",
    ),
    (
        re.compile(r"\bgit\s+push\b[^\n]*\s(--force(?!-with-lease)\b|-f\b)", re.IGNORECASE),
        "force-push can overwrite remote/shared history",
    ),
    (
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE is destructive to the database schema/data",
    ),
    (
        re.compile(r"\b(rm|del|remove-item)\b[^\n]*\.(db|sqlite3?|sqlite)\b", re.IGNORECASE),
        "deleting the sqlite database file",
    ),
]

SECRET_NAME_PATTERN = r"(ANTHROPIC_API_KEY|API_KEY|SECRET(_KEY)?|ACCESS_TOKEN|TOKEN|PASSWORD|PRIVATE_KEY)"
SECRET_REF_PATTERN = (
    rf"(\$env:{SECRET_NAME_PATTERN}|\${SECRET_NAME_PATTERN}\b"
    rf"|%{SECRET_NAME_PATTERN}%|\$\{{{SECRET_NAME_PATTERN}\}})"
)
SECRET_LEAK_RULES = [
    (
        re.compile(
            rf"\b(echo|print|write-output|cat|type)\b[^\n]*{SECRET_REF_PATTERN}",
            re.IGNORECASE,
        ),
        "printing what looks like a secret/API key to the console",
    ),
]


def find_violation(command: str):
    """Return the reason string for the first matching destructive/secret-leak rule, else None."""
    for pattern, reason in DESTRUCTIVE_RULES + SECRET_LEAK_RULES:
        if pattern.search(command):
            return reason
    return None


def main() -> None:
    """Read the PreToolUse Bash payload from stdin and block disallowed commands, else allow."""
    payload = json.loads(sys.stdin.read() or "{}")
    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""

    reason = find_violation(command)
    if reason:
        block(EVENT, reason, extra=command.strip()[:200])

    allow(EVENT)


if __name__ == "__main__":
    main()
