"""Connect to the local Expense MCP server and exercise its overview tool."""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]


async def verify() -> None:
    """Connect over MCP stdio, discover tools, and call the expense overview tool."""
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(PROJECT_ROOT / "tools" / "expense_mcp_server.py")],
        cwd=PROJECT_ROOT,
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("get_expense_overview", {})

    print(
        json.dumps(
            {
                "tools": [tool.name for tool in tools.tools],
                "result": result.structured_content,
                "is_error": result.is_error,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(verify())
