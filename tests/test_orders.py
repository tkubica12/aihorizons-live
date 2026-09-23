import json
from pathlib import Path

import pytest
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError
from starlette.testclient import TestClient

from pizza_mcp import order_seed, orders
from pizza_mcp.order_server import app, mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeCursor:
    def __init__(self, customer_exists=True):
        self.customer_exists = customer_exists
        self.statements = []
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        if "FROM demo_customer WHERE id" in sql:
            self.result = {"exists": 1} if self.customer_exists else None
        elif "FROM demo_order WHERE id" in sql:
            self.result = None
        elif "FROM demo_order WHERE customer_id" in sql and "ORDER BY" in sql:
            self.result = []
        elif "FROM demo_order o JOIN" in sql:
            self.result = []
        elif "FROM demo_order WHERE customer_id" in sql:
            self.result = {
                "order_count": 0, "delivered_count": 0, "cancelled_count": 0,
                "delivered_total_czk": 0, "first_order_at": None, "last_order_at": None,
            }

    def fetchone(self):
        return self.result

    def fetchall(self):
        return self.result


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def cursor(self):
        return self.fake_cursor


def test_order_fixture_validates_references_and_quantities(tmp_path):
    data = order_seed.load_orders()
    assert len(data["customers"]) == 3
    assert len(data["orders"]) == 6
    data["orders"][0]["items"][0]["quantity"] = 0
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid pizza item"):
        order_seed.load_orders(path)


def test_customer_scoping_filters_and_missing_order(monkeypatch):
    cursor = FakeCursor()
    monkeypatch.setattr(orders, "connect", lambda: FakeConnection(cursor))
    response = orders.list_orders("demo-anna", "delivered", 4)
    assert response["orders"] == []
    sql, params = cursor.statements[-1]
    assert "customer_id = %s AND status = %s" in sql
    assert params == ["demo-anna", "delivered", 4]
    with pytest.raises(ToolError, match="zvolený demo profil"):
        orders.get_order("demo-anna", "ORD-002")
    assert cursor.statements[-1][1] == ("ORD-002", "demo-anna")
    with pytest.raises(ToolError, match="Neznámý stav"):
        orders.list_orders("demo-anna", "unknown")
    with pytest.raises(ToolError, match="Limit"):
        orders.favorite_pizzas("demo-anna", 21)
    cursor.customer_exists = False
    with pytest.raises(ToolError, match="neexistuje"):
        orders.order_summary("not-a-customer")


def test_aggregations_use_delivered_orders(monkeypatch):
    cursor = FakeCursor()
    monkeypatch.setattr(orders, "connect", lambda: FakeConnection(cursor))
    assert orders.favorite_pizzas("demo-anna")["basis"] == "delivered_orders_only"
    assert "o.status = 'delivered'" in cursor.statements[-1][0]
    assert orders.order_summary("demo-anna")["delivered_total_czk"] == 0
    assert "FILTER (WHERE status = 'delivered')" in cursor.statements[-1][0]


@pytest.mark.anyio
async def test_separate_mcp_has_structured_tools(monkeypatch):
    monkeypatch.setattr(orders, "list_customers", lambda: {
        "customers": [{"id": "demo-anna", "display_name": "Anna (demo)"}],
        "count": 1, "is_demo_data": True,
    })
    async with Client(mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools.tools} == {
            "list_demo_customers", "list_customer_orders", "get_customer_order",
            "favorite_pizzas", "customer_order_summary",
        }
        assert all(tool.output_schema for tool in tools.tools)
        contract = json.loads(
            (Path(__file__).parents[1] / "Docs" / "Contracts" / "order-history.mcp.json")
            .read_text(encoding="utf-8")
        )
        assert {tool["name"] for tool in contract["tools"]} == {
            tool.name for tool in tools.tools
        }
        result = await client.call_tool("list_demo_customers", {})
        assert result.structured_content["customers"][0]["id"] == "demo-anna"


def test_order_http_requires_token(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("MCP_API_TOKEN", "test-token")
    with TestClient(app) as client:
        assert client.get("/healthz").status_code == 503
        assert client.post("/mcp", json={}).status_code == 401
