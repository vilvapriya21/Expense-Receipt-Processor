# Assignment evidence index

| Mandatory item | Status | Evidence |
|---|---|---|
| `CLAUDE.md` | Complete | Root `CLAUDE.md` documents current architecture, rules, skills, agents, hooks, MCP, commands, and Definition of Done |
| Project rules | Complete | `.claude/rules/*.md`; current filenames are referenced by `CLAUDE.md` |
| Reusable skill | Used | `.claude/skills/fastapi-react-feature-scaffold/`; `reusable-skill-usage.md`; receipts-slice review in `docs/reviews/` |
| Project-specific skill | Used | `.claude/skills/receipt-extraction/` and its extraction fixtures |
| Test-engineer subagent | Used | `.claude/agents/test-engineer.md`; backend test suite |
| Standards-reviewer subagent | Used | `.claude/agents/standards-reviewer.md`; reports under `docs/reviews/` |
| MCP server/tool | Connected and invoked | `.mcp.json`; `tools/expense_mcp_server.py`; `tools/verify_expense_mcp.py`; `mcp-expense-data.md` |
| Pre-hook | Used | `.claude/hooks/guard_writes.py`, `guard_bash.py`; `hooks.md` |
| Post-hook | Used | `.claude/hooks/format_and_lint.py`, `track_test_runs.py`; `hooks.md` |
| Cognine plugins | Enabled and used | `.claude/settings.local.json`; standards-reviewer instructions and review report |
| Functional integration | Complete | Feature implementation, tests, MCP live-data result, and evidence above |

The evidence files record demonstrated behavior. They do not list planned or unconnected
integrations as complete.
