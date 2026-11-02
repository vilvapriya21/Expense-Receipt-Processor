# MCP evidence — `expense-data`

Demonstrated on 2026-10-30 using the project-scoped server declared in `.mcp.json`.

## Integration

- Server: `tools/expense_mcp_server.py`
- Transport: MCP stdio
- Tool: `get_expense_overview`
- Safety: opens `backend/data/app.db` with SQLite `mode=ro`; exposes no arbitrary SQL
- Client verifier: `tools/verify_expense_mcp.py`

Claude Code health check reported:

```text
expense-data: python ./tools/expense_mcp_server.py - Connected
```

The verifier then performed initialization, tool discovery, and a real tool call:

```json
{
  "tools": ["get_expense_overview"],
  "result": {
    "users": 3,
    "categories": 7,
    "receipts": 6,
    "receipts_by_status": [
      {"status": "APPROVED", "count": 4},
      {"status": "EXTRACTED", "count": 1},
      {"status": "SUBMITTED", "count": 1}
    ]
  },
  "is_error": false
}
```

This demonstrates integration and meaningful use against live local application data,
not configuration alone.
