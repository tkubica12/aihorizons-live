import json

import pytest
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError
from starlette.testclient import TestClient

from pizza_mcp import orders
from pizza_mcp.hello_agent import app as hello_app, graph
from pizza_mcp.staff_server import app as staff_app, mcp as staff_mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


class Cursor:
    def __init__(self):
        self.queries = []
        self.result = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, sql, params=()):
        self.queries.append((sql, params))

    def fetchall(self):
        return self.result

    def fetchone(self):
        return None


class Connection:
    def __init__(self, cursor):
        self.value = cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def cursor(self):
        return self.value


def test_staff_orders_across_customers_are_bounded(monkeypatch):
    cursor = Cursor()
    monkeypatch.setattr(orders, "connect", lambda: Connection(cursor))
    assert orders.list_staff_orders("preparing", 5)["count"] == 0
    query, params = cursor.queries[-1]
    assert "JOIN demo_customer" in query
    assert "customer_id = %s" not in query
    assert params == ["preparing", 5]
    with pytest.raises(ToolError, match="Limit"):
        orders.list_staff_orders(limit=51)
    with pytest.raises(ToolError, match="Neznámý"):
        orders.list_staff_orders("made-up")
    with pytest.raises(ToolError, match="neexistuje"):
        orders.get_staff_order("ORD-404")
    assert cursor.queries[-1][1] == ("ORD-404",)


@pytest.mark.anyio
async def test_staff_tools_separate_from_customer_mcp():
    from pizza_mcp.order_server import mcp as customer_mcp

    async with Client(staff_mcp) as staff, Client(customer_mcp) as customer:
        staff_tools = await staff.list_tools()
        customer_tools = await customer.list_tools()
    assert {tool.name for tool in staff_tools.tools} == {
        "list_staff_orders", "get_staff_order",
    }
    assert not {tool.name for tool in staff_tools.tools} & {
        tool.name for tool in customer_tools.tools
    }
    with open("Docs/Contracts/staff-orders.mcp.json", encoding="utf-8") as contract:
        assert {tool["name"] for tool in json.load(contract)["tools"]} == {
            tool.name for tool in staff_tools.tools
        }


def test_staff_http_requires_its_own_token(monkeypatch):
    monkeypatch.setenv("MCP_API_TOKEN", "staff-only")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with TestClient(staff_app) as client:
        assert client.get("/healthz").status_code == 503
        assert client.post("/mcp", json={}, headers={"Authorization": "Bearer customer-token"}).status_code == 401


def test_external_hello_graph_and_auth(monkeypatch):
    monkeypatch.setenv("HELLO_API_TOKEN", "hello-only")
    assert "Ahoj" in graph.invoke({"message": "ahoj", "response": ""})["response"]
    with TestClient(hello_app) as client:
        assert client.post("/chat", json={"message": "ahoj"}).status_code == 401
        response = client.post("/chat", json={"message": "ahoj"},
                               headers={"Authorization": "Bearer hello-only"})
        assert response.status_code == 200
        assert "Ahoj" in response.json()["response"]
        assert client.post("/chat", json={"message": ""},
                           headers={"Authorization": "Bearer hello-only"}).status_code == 400


@pytest.mark.anyio
async def test_staff_graph_accepts_discovered_toolbox_tools(monkeypatch):
    from langchain_core.tools import StructuredTool
    from pizza_mcp import staff_agent

    async def fake_tool(**kwargs):
        return "ok"

    async def fake_load_tools(endpoint, credential):
        return [
            StructuredTool.from_function(
                coroutine=fake_tool, name=name, description=name,
                args_schema={"type": "object", "properties": {}},
            )
            for name in ("tool_search", "call_tool", "pizza_staff_orders___list_staff_orders")
        ]

    monkeypatch.setattr(staff_agent, "load_tools", fake_load_tools)
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://example.test/api/projects/demo")
    monkeypatch.setenv("MODEL_DEPLOYMENT_NAME", "gpt-5.4")
    graph = await staff_agent.build_graph()
    assert "tools" in graph.nodes
