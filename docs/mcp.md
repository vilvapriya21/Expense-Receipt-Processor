# Expense data MCP server

The project registers one local, read-only MCP server in `.mcp.json`:

```json
{
  "mcpServers": {
    "expense-data": {
      "command": "python",
      "args": ["./tools/expense_mcp_server.py"]
    }
  }
}
```

The server exposes `get_expense_overview`, which reads the local SQLite database in
read-only mode and returns user, category, receipt, and receipt-status counts. This is a
meaningful operational check for confirming seed data and workflow state without giving
an agent arbitrary SQL or write access.

Prerequisites:

1. Install backend development dependencies: `pip install -e ".[dev]"`.
2. Run migrations and `python scripts/seed.py` from `backend/`.
3. Start Claude Code from the repository root so it loads `.mcp.json`.

Verify the complete MCP handshake, tool discovery, and tool call with:

```powershell
python tools/verify_expense_mcp.py
```

The verification client connects over MCP stdio and invokes the tool. It does not query
the database directly.
