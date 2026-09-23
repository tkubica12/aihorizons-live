import json
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from pizza_mcp import catalog
from pizza_mcp.seed import load_fixture


def test_fixture_has_twelve_consistent_pizzas():
    data = load_fixture()
    assert len(data["pizzas"]) == 12
    assert len(data["allergens"]) == 14
    assert {p["id"] for p in data["pizzas"]} == {
        pdf.stem for pdf in (Path(__file__).parents[1] / "sample-data" / "pizza-pdfs").glob("*.pdf")
    }
    assert any(not ingredient.get("profile_complete", True) for ingredient in data["ingredients"])


def test_fixture_rejects_missing_ingredient(tmp_path):
    data = load_fixture()
    data["pizzas"][0]["recipe"]["missing"] = 4
    fixture = tmp_path / "invalid.json"
    fixture.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown recipe ingredient"):
        load_fixture(fixture)


class FakeCursor:
    def __init__(self, results):
        self.results = iter(results)
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, statement, params):
        self.calls.append((statement, params))

    def fetchone(self):
        return next(self.results)

    def fetchall(self):
        return next(self.results)


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_instance = cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def cursor(self):
        return self.cursor_instance


def test_filter_is_bound_and_bounded(monkeypatch):
    cursor = FakeCursor([[{"id": "01-margherita"}]])
    monkeypatch.setattr(catalog, "connect", lambda: FakeConnection(cursor))
    result = catalog.list_pizzas(category="klasika", query="marg%' OR 1=1 --", limit=2)
    assert result["count"] == 1
    statement, params = cursor.calls[0]
    assert "ORDER BY name LIMIT %s" in statement
    assert "OR 1=1" not in statement
    assert params == ["klasika", "%marg%' OR 1=1 --%", 2]
    with pytest.raises(ToolError, match="Limit"):
        catalog.list_pizzas(limit=51)


def test_declared_and_uncertain_allergens(monkeypatch):
    pizza = {"id": "03-napoli", "declared_allergens": [
        {"number": 1, "name": "Lepek"}, {"number": 4, "name": "Ryby"}],
        "uncertain_ingredients": [{"ingredient": "Kapary", "note": "Ověřit nálev"}],
        "safety_note": "Nejde o potvrzení bezalergennosti."}
    monkeypatch.setattr(catalog, "get_pizza", lambda pizza_id: pizza)
    monkeypatch.setattr(catalog, "connect",
                        lambda: FakeConnection(FakeCursor([{"name": "Ryby"}])))
    assert catalog.check_allergen("03-napoli", 4)["status"] == "declared"
    monkeypatch.setattr(catalog, "connect",
                        lambda: FakeConnection(FakeCursor([{"name": "Mléko"}])))
    result = catalog.check_allergen("03-napoli", 7)
    assert result["status"] == "uncertain"
    assert result["uncertain_ingredients"][0]["ingredient"] == "Kapary"
    pizza["uncertain_ingredients"] = []
    assert catalog.check_allergen("03-napoli", 7)["status"] == "not_declared_in_demo_recipe"
    with pytest.raises(ToolError, match="1 a 14"):
        catalog.check_allergen("03-napoli", 15)


def test_unknown_pizza_is_error(monkeypatch):
    monkeypatch.setattr(catalog, "connect",
                        lambda: FakeConnection(FakeCursor([None])))
    with pytest.raises(ToolError, match="neexistuje"):
        catalog.get_pizza("neexistuje")
