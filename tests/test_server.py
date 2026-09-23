import json
from pathlib import Path

import pytest
from mcp import Client
from starlette.testclient import TestClient

from pizza_mcp import catalog
from pizza_mcp.server import app, mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_mcp_tools_have_structured_results(monkeypatch):
    monkeypatch.setattr(catalog, "list_pizzas", lambda *args: {
        "pizzas": [{"id": "01-margherita", "name": "Margherita",
                    "category": "klasika", "description": "Demo",
                    "price_czk": 189, "available": True}],
        "count": 1, "limit": 20, "source": "demo_catalog", "is_demo_data": True,
    })
    monkeypatch.setattr(catalog, "get_pizza", lambda pizza_id: {
        "id": pizza_id, "name": "Margherita", "category": "klasika",
        "description": "Demo", "price_czk": 189, "available": True,
        "updated_at": "2026-09-23", "ingredients": [],
        "declared_allergens": [{"number": 1, "name": "Lepek"}],
        "uncertain_ingredients": [], "is_demo_data": True,
        "source": "demo_catalog", "safety_note": "Modelová deklarace.",
    })
    monkeypatch.setattr(catalog, "check_allergen", lambda pizza_id, number: {
        "pizza_id": pizza_id, "allergen_number": number, "allergen_name": "Lepek",
        "status": "declared", "uncertain_ingredients": [],
        "source": "demo_catalog", "is_demo_data": True, "safety_note": "Demo",
    })
    monkeypatch.setattr(catalog, "list_ingredients", lambda: {
        "ingredients": [], "count": 0, "source": "demo_catalog", "is_demo_data": True,
    })
    monkeypatch.setattr(catalog, "list_allergens", lambda: {
        "allergens": [], "count": 0, "source": "demo_catalog", "is_demo_data": True,
    })
    async with Client(mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools.tools} == {
            "list_pizzas", "get_pizza", "check_allergen",
            "list_ingredients", "list_allergens",
        }
        contract = json.loads(
            (Path(__file__).parents[1] / "Docs" / "Contracts" / "pizza-catalog.mcp.json")
            .read_text(encoding="utf-8")
        )
        assert {tool["name"] for tool in contract["tools"]} == {
            tool.name for tool in tools.tools
        }
        assert all(tool.output_schema for tool in tools.tools)
        result = await client.call_tool("list_pizzas", {"category": "klasika"})
        assert not result.is_error
        assert result.structured_content["pizzas"][0]["id"] == "01-margherita"
        result = await client.call_tool("check_allergen", {
            "pizza_id": "01-margherita", "allergen_number": 1,
        })
        assert result.structured_content["status"] == "declared"


def test_http_requires_token_and_health_reports_missing_configuration(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("MCP_API_TOKEN", "test-token")
    with TestClient(app) as client:
        assert client.get("/healthz").status_code == 503
        assert client.post("/mcp", json={}).status_code == 401
        assert client.post("/mcp", json={},
                           headers={"Authorization": "Bearer incorrect"}).status_code == 401
