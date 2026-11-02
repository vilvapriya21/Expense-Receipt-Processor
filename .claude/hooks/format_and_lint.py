#!/usr/bin/env python3
"""PostToolUse hook for Edit|Write|MultiEdit.

After a backend .py file is written, runs `ruff check --fix`, `black`, then
`mypy` on it. After a frontend .ts/.tsx file is written, runs `prettier --write`
then `eslint --fix` on it. If problems remain, prints them to stderr and exits 2
so Claude sees them immediately. Cross-platform: stdlib only (subprocess),
reads hook JSON from stdin. Missing tools are skipped (logged), not fatal —
this project may not have its toolchain installed yet.
"""

import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hook_common import log  # noqa: E402

EVENT = "PostToolUse:format_and_lint"


def normalized(path: str) -> str:
    """Return path with backslashes converted to forward slashes, for uniform matching."""
    return path.replace("\\", "/")


def run(cmd: list[str], cwd: str | None = None) -> tuple[bool, str]:
    """Run a command, returning (tool_was_found, combined_output). Never raises."""
    exe = cmd[0]
    if shutil.which(exe) is None:
        return False, f"{exe} not found on PATH; skipped"
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=cwd)
    except (subprocess.SubprocessError, OSError) as exc:
        return True, f"error running {' '.join(cmd)}: {exc}"
    output = (result.stdout or "") + (result.stderr or "")
    return True, output.strip()


def backend_root(file_path: str) -> str | None:
    """Return the backend/ directory containing file_path, so tools run with the right cwd."""
    parts = normalized(os.path.abspath(file_path)).split("/")
    if "backend" not in parts:
        return None
    index = parts.index("backend")
    return "/".join(parts[: index + 1])


def handle_backend_python(file_path: str) -> list[str]:
    """Run ruff --fix, black, then mypy --strict on a backend .py file. Return remaining problems."""
    problems = []
    cwd = backend_root(file_path)

    found, output = run(["ruff", "check", "--fix", file_path], cwd=cwd)
    if found and output:
        log(EVENT, "ran", "ruff check --fix", extra=file_path)

    found, output = run(["black", file_path], cwd=cwd)
    if found and output:
        log(EVENT, "ran", "black", extra=file_path)

    found, output = run(["mypy", "--strict", file_path], cwd=cwd)
    if found and output and "Success: no issues found" not in output:
        problems.append(f"mypy --strict errors remain in {file_path}:\n{output}")
    log(EVENT, "ran", "mypy --strict", extra=file_path)

    return problems


def handle_frontend_ts(file_path: str) -> list[str]:
    """Run prettier --write then eslint --fix on a frontend .ts/.tsx file. Return remaining problems."""
    problems = []

    found, output = run(["prettier", "--write", file_path])
    if found and output:
        log(EVENT, "ran", "prettier --write", extra=file_path)

    found, output = run(["eslint", "--fix", file_path])
    if found and output:
        problems.append(f"eslint errors remain in {file_path}:\n{output}")
    log(EVENT, "ran", "eslint --fix", extra=file_path)

    return problems


def main() -> None:
    """Read the PostToolUse payload from stdin, format/lint the written file, report problems."""
    payload = json.loads(sys.stdin.read() or "{}")
    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path")

    if not file_path:
        sys.exit(0)

    path = normalized(file_path)
    problems: list[str] = []

    if path.endswith(".py") and "backend/" in path:
        problems = handle_backend_python(file_path)
    elif path.endswith((".ts", ".tsx")) and "frontend/" in path:
        problems = handle_frontend_ts(file_path)
    else:
        sys.exit(0)

    if problems:
        log(EVENT, "problems_remain", "; ".join(p.splitlines()[0] for p in problems), extra=file_path)
        sys.stderr.write("\n\n".join(problems) + "\n")
        sys.exit(2)

    log(EVENT, "clean", "no remaining problems", extra=file_path)
    sys.exit(0)


if __name__ == "__main__":
    main()
