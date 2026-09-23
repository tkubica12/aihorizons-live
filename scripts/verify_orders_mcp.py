"""Verify a deployed order-history MCP against real seeded database rows."""

import asyncio
import os

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    base_url = os.environ["ORDER_MCP_URL"].rstrip("/")
    url = base_url + "/mcp"
    token = os.environ["MCP_API_TOKEN"]
    async with httpx2.AsyncClient() as anonymous:
        assert (await anonymous.get(url)).status_code == 401
    async with httpx2.AsyncClient(
        headers={"Authorization": f"Bearer {token}"},
        timeout=httpx2.Timeout(30.0, read=120.0),
    ) as http:
        response = await http.get(base_url + "/healthz")
        response.raise_for_status()
        assert response.json()["status"] == "ok"
        async with Client(streamable_http_client(url, http_client=http)) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "list_demo_customers", "list_customer_orders", "get_customer_order",
                "favorite_pizzas", "customer_order_summary",
            }

            async def call(name, args):
                result = await client.call_tool(name, args)
                assert not result.is_error, f"{name}: {result.content}"
                assert result.structured_content is not None
                return result.structured_content

            customers = await call("list_demo_customers", {})
            assert customers["count"] == 3
            anna = await call("list_customer_orders", {
                "customer_id": "demo-anna", "limit": 20,
            })
            assert anna["count"] == 3
            order = await call("get_customer_order", {
                "customer_id": "demo-anna", "order_id": "ORD-001",
            })
            assert len(order["items"]) == 2
            assert order["total_czk"] == sum(i["line_total_czk"] for i in order["items"])
            favorites = await call("favorite_pizzas", {"customer_id": "demo-anna"})
            assert favorites["basis"] == "delivered_orders_only"
            assert favorites["pizzas"][0]["pizza_id"] == "01-margherita"
            summary = await call("customer_order_summary", {"customer_id": "demo-anna"})
            assert summary["order_count"] == 3 and summary["delivered_count"] == 3
            other = await client.call_tool("get_customer_order", {
                "customer_id": "demo-boris", "order_id": "ORD-001",
            })
            assert other.is_error
            print("Order MCP ověřeno: 5 nástrojů, 3 profily a fiktivní historie.")


if __name__ == "__main__":
    asyncio.run(main())
