# Hooks evidence — 2026-10-30

Demonstration of the `PreToolUse` and `PostToolUse` hooks configured in
`.claude/settings.json` (scripts in `.claude/hooks/`).

## 1. PreToolUse blocks a write to `.env`

**Action:** Claude attempted to write `backend/.env` via the `Write` tool.

**Hook:** `guard_writes.py`, matcher `Edit|Write|MultiEdit`.

**Result:** blocked, exit code 2, file never written.

```
PreToolUse:Write hook error: [python .claude/hooks/guard_writes.py]: BLOCKED: refusing to write to env file: C:\Users\Priya Koma\Desktop\Claude_workshop\Expense Receipt Processor\backend\.env
```

**Log entry** (`.claude/logs/hooks.log`):

```
[2026-10-30T14:40:40] event=PreToolUse:guard_writes decision=blocked reason=refusing to write to env file: C:\Users\Priya Koma\Desktop\Claude_workshop\Expense Receipt Processor\backend\.env extra=Write
```

## 2. PostToolUse auto-fixes a badly formatted backend Python file

**Action:** Claude wrote `backend/src/app/routers/demo.py` with an unused
import and inconsistent spacing:

```python
import os
import sys


def   add(x,y):
    z=x+y
    return z
```

**Hook:** `format_and_lint.py`, matcher `Edit|Write|MultiEdit` — detects the
file is `.py` under `backend/`, runs `ruff check --fix`, then `black`, then
`mypy`.

**Result:** file auto-corrected in place (unused `import os`/`import sys`
removed by ruff, spacing/formatting normalized by black), `mypy` reported no
remaining issues, hook exited 0 (no action needed from Claude):

```python
def add(x, y):
    z = x + y
    return z
```

**Log entries** (`.claude/logs/hooks.log`):

```
[2026-10-30T14:40:44] event=PostToolUse:format_and_lint decision=ran reason=ruff check --fix extra=...\backend\src\app\routers\demo.py
[2026-10-30T14:40:46] event=PostToolUse:format_and_lint decision=ran reason=black extra=...\backend\src\app\routers\demo.py
[2026-10-30T14:40:47] event=PostToolUse:format_and_lint decision=ran reason=mypy extra=...\backend\src\app\routers\demo.py
[2026-10-30T14:40:47] event=PostToolUse:format_and_lint decision=clean reason=no remaining problems extra=...\backend\src\app\routers\demo.py
```

Note: the installed Cognine `python-fastapi-coding-standards-best-practices`
plugin also ran its own (separate, pre-existing) PostToolUse hook on this
same write and flagged unrelated standards issues (missing `APIRouter`,
missing docstring) — that plugin hook is independent of the hooks built here
and is expected to fire on every `.py` write regardless of this project's
own hook configuration.

## Other rules verified by direct pipe-testing (not re-demonstrated live)

All of the following were exercised by piping synthetic hook JSON into the
scripts directly (`echo '<json>' | python .claude/hooks/<script>.py`) before
wiring them into `settings.json`, and behaved as specified:

- `guard_writes.py`: blocks `*.db` / `*.sqlite*` files, writes under
  `uploads/`, and edits to an *existing* `alembic/versions/*.py` file (a new,
  not-yet-existing migration file is allowed).
- `guard_bash.py`: blocks `rm -rf /` (and other root/home/project-root
  recursive deletes), `git push --force` / `-f` (but allows
  `--force-with-lease`), `DROP TABLE ...`, deleting a `.db`/`.sqlite` file,
  and `echo $ANTHROPIC_API_KEY` (and similarly named secret env vars).
- `track_test_runs.py` (PostToolUse, matcher `Bash`) + `stop_test_reminder.py`
  (Stop): a session with no `pytest` invocation yet gets a `systemMessage`
  reminder on Stop; after a `pytest` command runs, the reminder is
  suppressed for the rest of that session.

## How this was proven live

Both demonstrations above were run as the actual `Write` tool calls Claude
Code presents to the user — not simulated — so the hook JSON blocks and
file content shown are real tool output, not predicted text.
