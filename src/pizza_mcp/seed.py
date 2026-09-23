"""Load the versioned fictional catalog into PostgreSQL."""

import json
import os
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "sample-data" / "catalog.json"
SCHEMA = ROOT / "database" / "001_catalog.sql"


def load_fixture(path: Path = FIXTURE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    ingredients = {item["id"] for item in data["ingredients"]}
    allergens = {item["number"] for item in data["allergens"]}
    pizzas = {item["id"] for item in data["pizzas"]}
    if len(ingredients) != len(data["ingredients"]) or len(pizzas) != len(data["pizzas"]):
        raise ValueError("Duplicate ingredient or pizza ID in catalog")
    if allergens != set(range(1, 15)):
        raise ValueError("The catalog must define all 14 numbered allergens")
    for ingredient in data["ingredients"]:
        if not set(ingredient["allergens"]) <= allergens:
            raise ValueError(f"Unknown allergen in {ingredient['id']}")
    for pizza in data["pizzas"]:
        if not pizza["recipe"] or not set(pizza["recipe"]) <= ingredients:
            raise ValueError(f"Missing or unknown recipe ingredient in {pizza['id']}")
        if "dough" not in pizza["recipe"] or any(grams <= 0 for grams in pizza["recipe"].values()):
            raise ValueError(f"Invalid recipe in {pizza['id']}")
    return data


def seed(connection: psycopg.Connection, data: dict) -> None:
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA.read_text(encoding="utf-8"))
            for allergen in data["allergens"]:
                cursor.execute(
                    """INSERT INTO allergen (number, name) VALUES (%s, %s)
                       ON CONFLICT (number) DO UPDATE SET name = EXCLUDED.name""",
                    (allergen["number"], allergen["name"]),
                )
            for ingredient in data["ingredients"]:
                cursor.execute(
                    """INSERT INTO ingredient (id, name, allergen_profile_complete, profile_note)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name,
                         allergen_profile_complete = EXCLUDED.allergen_profile_complete,
                         profile_note = EXCLUDED.profile_note""",
                    (
                        ingredient["id"], ingredient["name"],
                        ingredient.get("profile_complete", True),
                        ingredient.get("profile_note", ""),
                    ),
                )
                cursor.execute(
                    "DELETE FROM ingredient_allergen WHERE ingredient_id = %s",
                    (ingredient["id"],),
                )
                for number in ingredient["allergens"]:
                    cursor.execute(
                        "INSERT INTO ingredient_allergen (ingredient_id, allergen_number) VALUES (%s, %s)",
                        (ingredient["id"], number),
                    )
            for pizza in data["pizzas"]:
                cursor.execute(
                    """INSERT INTO pizza (id, name, category, description, price_czk, available)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name,
                         category = EXCLUDED.category, description = EXCLUDED.description,
                         price_czk = EXCLUDED.price_czk, available = EXCLUDED.available,
                         updated_at = now()""",
                    (
                        pizza["id"], pizza["name"], pizza["category"],
                        pizza["description"], pizza["price_czk"], pizza["available"],
                    ),
                )
                cursor.execute("DELETE FROM pizza_ingredient WHERE pizza_id = %s", (pizza["id"],))
                for ingredient_id, grams in pizza["recipe"].items():
                    cursor.execute(
                        "INSERT INTO pizza_ingredient (pizza_id, ingredient_id, grams) VALUES (%s, %s, %s)",
                        (pizza["id"], ingredient_id, grams),
                    )


def main() -> None:
    url = os.environ["DATABASE_URL"]
    data = load_fixture()
    with psycopg.connect(url) as connection:
        seed(connection, data)
    print(f"Seeded {len(data['pizzas'])} pizzas, {len(data['ingredients'])} ingredients.")


if __name__ == "__main__":
    main()
