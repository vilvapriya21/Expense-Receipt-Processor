"""Read-only MCP tools for inspecting Expense Receipt Processor data."""

import sqlite3
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from typing_extensions import TypedDict

DATABASE_PATH = Path(__file__).resolve().parents[1] / "backend" / "data" / "app.db"


class ReceiptStatusCount(TypedDict):
    """Receipt count grouped under one workflow status."""

    status: str
    count: int


class ExpenseOverview(TypedDict):
    """Read-only operational overview returned to MCP clients."""

    users: int
    categories: int
    receipts: int
    receipts_by_status: list[ReceiptStatusCount]


server = MCPServer(
    "expense-receipt-processor",
    instructions="Use these read-only tools to inspect seeded application data.",
)


@server.tool()
def get_expense_overview() -> ExpenseOverview:
    """Return user, category, receipt, and status counts from the app database."""
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(
            "Application database not found; run migrations and the seed script first."
        )

    database_uri = f"file:{DATABASE_PATH.as_posix()}?mode=ro"
    with sqlite3.connect(database_uri, uri=True) as connection:
        users = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        categories = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        receipts = connection.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
        status_rows = connection.execute(
            "SELECT status, COUNT(*) FROM receipts GROUP BY status ORDER BY status"
        ).fetchall()

    return {
        "users": int(users),
        "categories": int(categories),
        "receipts": int(receipts),
        "receipts_by_status": [
            {"status": str(status), "count": int(count)}
            for status, count in status_rows
        ],
    }


if __name__ == "__main__":
    server.run()
