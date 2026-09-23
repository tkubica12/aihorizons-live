"""Generate the machine-readable tool contract from the running MCP definition."""

import asyncio
import json
from pathlib import Path

from mcp import Client

from pizza_mcp.order_server import mcp as order_mcp
from pizza_mcp.server import mcp


OUTPUT = Path(__file__).resolve().parents[1] / "Docs" / "Contracts" / "pizza-catalog.mcp.json"
ORDER_OUTPUT = OUTPUT.with_name("order-history.mcp.json")


async def main() -> None:
    for name, server, output in (
        ("pizza-catalog", mcp, OUTPUT),
        ("order-history", order_mcp, ORDER_OUTPUT),
    ):
        async with Client(server) as client:
            result = await client.list_tools()
        contract = {
            "name": name,
            "version": "0.1.0",
            "transport": "streamable-http",
            "path": "/mcp",
            "tools": [tool.model_dump(by_alias=True, exclude_none=True) for tool in result.tools],
        }
        output.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
