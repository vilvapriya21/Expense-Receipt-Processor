#!/usr/bin/env python3
"""PreToolUse hook for Edit|Write|MultiEdit.

Blocks writes to secrets, databases, upload storage, and existing (immutable)
Alembic migration files. Cross-platform: stdlib only, reads hook JSON from stdin.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_common import allow, block  # noqa: E402

EVENT = "PreToolUse:guard_writes"

DB_EXTENSIONS = (".db", ".sqlite", ".sqlite3")


def normalized(path: str) -> str:
    """Return path with backslashes converted to forward slashes, for uniform matching."""
    return path.replace("\\", "/").strip()


def is_env_file(path: str) -> bool:
    """Return True if path points at a .env or .env.* file."""
    base = os.path.basename(path)
    return base == ".env" or base.startswith(".env.")


def is_db_file(path: str) -> bool:
    """Return True if path has a sqlite/db extension."""
    return path.lower().endswith(DB_EXTENSIONS)


def is_under_uploads(path: str) -> bool:
    """Return True if path lives inside an uploads/ directory."""
    parts = path.split("/")
    return "uploads" in parts[:-1] or path.startswith("uploads/")


def is_existing_alembic_migration(path: str, project_root: str) -> bool:
    """Return True if path is an Alembic migration file that already exists on disk."""
    if "/alembic/versions/" not in f"/{path}":
        return False
    if not path.endswith(".py"):
        return False
    candidate = path if os.path.isabs(path) else os.path.join(project_root, path)
    return os.path.exists(candidate)


def collect_file_paths(tool_input: dict) -> list[str]:
    """Return the target file path(s) from an Edit/Write/MultiEdit tool_input payload."""
    file_path = tool_input.get("file_path")
    return [file_path] if file_path else []


def main() -> None:
    """Read the PreToolUse payload from stdin and block disallowed writes, else allow."""
    payload = json.loads(sys.stdin.read() or "{}")
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    project_root = os.getcwd()

    for raw_path in collect_file_paths(tool_input):
        path = normalized(raw_path)

        if is_env_file(path):
            block(EVENT, f"refusing to write to env file: {raw_path}", extra=tool_name)
        if is_db_file(path):
            block(EVENT, f"refusing to write to a database file: {raw_path}", extra=tool_name)
        if is_under_uploads(path):
            block(EVENT, f"refusing to write inside uploads/: {raw_path}", extra=tool_name)
        if is_existing_alembic_migration(path, project_root):
            block(
                EVENT,
                f"refusing to modify an existing Alembic migration (immutable once applied): {raw_path}",
                extra=tool_name,
            )

    allow(EVENT)


if __name__ == "__main__":
    main()
