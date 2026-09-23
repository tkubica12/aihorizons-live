"""End-to-end check of the deployed MCP server from this computer."""

import asyncio
import os

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    url = os.environ["MCP_URL"].rstrip("/") + "/mcp"
    token = os.environ["MCP_API_TOKEN"]
    async with httpx2.AsyncClient() as anonymous:
        unauthorized = await anonymous.get(url)
        assert unauthorized.status_code == 401
    async with httpx2.AsyncClient(
        headers={"Authorization": f"Bearer {token}"},
        timeout=httpx2.Timeout(30.0, read=120.0),
    ) as http:
        response = await http.get(url.removesuffix("/mcp") + "/healthz")
        response.raise_for_status()
        assert response.json()["status"] == "ok"
        async with Client(streamable_http_client(url, http_client=http)) as client:
            tools = await client.list_tools()
            expected = {"list_pizzas", "get_pizza", "check_allergen",
                        "list_ingredients", "list_allergens"}
            assert {tool.name for tool in tools.tools} == expected
            results = {}
            for name, args in (
                ("list_pizzas", {"available_only": False}),
                ("list_ingredients", {}),
                ("list_allergens", {}),
                ("get_pizza", {"pizza_id": "01-margherita"}),
                ("check_allergen", {"pizza_id": "01-margherita", "allergen_number": 1}),
            ):
                result = await client.call_tool(name, args)
                assert not result.is_error, f"{name}: {result.content}"
                assert result.structured_content is not None
                results[name] = result.structured_content
            assert results["list_pizzas"]["count"] == 12
            assert results["list_ingredients"]["count"] == 27
            assert results["list_allergens"]["count"] == 14
            assert results["get_pizza"]["id"] == "01-margherita"
            assert results["check_allergen"]["status"] == "declared"
            assert any(item["id"] == "dough" for item in results["get_pizza"]["ingredients"])
            filtered = await client.call_tool("list_pizzas", {
                "category": "klasika", "query": "Margherita", "limit": 5,
            })
            assert not filtered.is_error
            assert [pizza["id"] for pizza in filtered.structured_content["pizzas"]] == [
                "01-margherita"
            ]
            uncertain = await client.call_tool("check_allergen", {
                "pizza_id": "03-napoli", "allergen_number": 3,
            })
            assert not uncertain.is_error
            assert uncertain.structured_content["status"] == "uncertain"
            print("MCP ověřeno: 5 nástrojů, 12 pizz, 27 surovin, 14 alergenů.")


if __name__ == "__main__":
    asyncio.run(main())
