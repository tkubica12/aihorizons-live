"""Bounded, read-only SQL queries over the demo catalog."""

import logging
import os

import psycopg
from mcp.server.mcpserver.exceptions import ToolError
from psycopg.rows import dict_row

from pizza_mcp.models import AllergenCheck, AllergenList, IngredientList, PizzaDetail, PizzaList


logger = logging.getLogger(__name__)


def connect() -> psycopg.Connection:
    url = os.environ["DATABASE_URL"]
    try:
        return psycopg.connect(url, row_factory=dict_row, connect_timeout=5)
    except psycopg.OperationalError as exc:
        logger.exception("Catalog database connection failed")
        raise ToolError("Databáze katalogu není dostupná.") from exc


def list_pizzas(category: str | None = None, query: str | None = None,
                available_only: bool = True, limit: int = 20) -> PizzaList:
    if not 1 <= limit <= 50:
        raise ToolError("Limit musí být mezi 1 a 50.")
    if category is not None:
        category = category.strip()
    if query is not None:
        query = query.strip()
    statement = (
        "SELECT id, name, category, description, price_czk, available "
        "FROM pizza WHERE TRUE"
    )
    params = []
    if category:
        statement += " AND category = %s"
        params.append(category)
    if query:
        statement += " AND name ILIKE %s"
        params.append(f"%{query}%")
    if available_only:
        statement += " AND available"
    statement += " ORDER BY name LIMIT %s"
    params.append(limit)
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(statement, params)
        pizzas = cursor.fetchall()
    return {"pizzas": pizzas, "count": len(pizzas), "limit": limit,
            "source": "demo_catalog", "is_demo_data": True}


def get_pizza(pizza_id: str) -> PizzaDetail:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """SELECT id, name, category, description, price_czk, available,
                      updated_at::text AS updated_at
               FROM pizza WHERE id = %s""",
            (pizza_id,),
        )
        pizza = cursor.fetchone()
        if pizza is None:
            raise ToolError(f"Pizza {pizza_id!r} v katalogu neexistuje.")
        cursor.execute(
            """SELECT i.id, i.name, pi.grams, i.allergen_profile_complete,
                      i.profile_note
               FROM pizza_ingredient pi JOIN ingredient i ON i.id = pi.ingredient_id
               WHERE pi.pizza_id = %s ORDER BY i.name""",
            (pizza_id,),
        )
        ingredients = cursor.fetchall()
        cursor.execute(
            """SELECT DISTINCT a.number, a.name
               FROM pizza_ingredient pi
               JOIN ingredient_allergen ia ON ia.ingredient_id = pi.ingredient_id
               JOIN allergen a ON a.number = ia.allergen_number
               WHERE pi.pizza_id = %s ORDER BY a.number""",
            (pizza_id,),
        )
        allergens = cursor.fetchall()
    unknown = [
        {"ingredient": item["name"], "note": item["profile_note"]}
        for item in ingredients if not item["allergen_profile_complete"]
    ]
    return {
        **pizza, "ingredients": ingredients, "declared_allergens": allergens,
        "uncertain_ingredients": unknown, "source": "demo_catalog",
        "is_demo_data": True,
        "safety_note": "Modelová deklarace; neúplné profily dodavatelských výrobků a křížová kontaminace nejsou vyloučeny.",
    }


def check_allergen(pizza_id: str, allergen_number: int) -> AllergenCheck:
    if not 1 <= allergen_number <= 14:
        raise ToolError("Číslo alergenu musí být mezi 1 a 14.")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT name FROM allergen WHERE number = %s", (allergen_number,))
        allergen = cursor.fetchone()
    if allergen is None:
        raise ToolError(f"Alergen {allergen_number} není v katalogu.")
    pizza = get_pizza(pizza_id)
    declared = any(a["number"] == allergen_number for a in pizza["declared_allergens"])
    status = "declared" if declared else (
        "uncertain" if pizza["uncertain_ingredients"] else "not_declared_in_demo_recipe"
    )
    return {
        "pizza_id": pizza_id, "allergen_number": allergen_number,
        "allergen_name": allergen["name"], "status": status,
        "uncertain_ingredients": pizza["uncertain_ingredients"],
        "safety_note": pizza["safety_note"], "source": "demo_catalog",
        "is_demo_data": True,
    }


def list_ingredients() -> IngredientList:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, name, allergen_profile_complete, profile_note FROM ingredient ORDER BY name"
        )
        ingredients = cursor.fetchall()
    return {"ingredients": ingredients, "count": len(ingredients),
            "source": "demo_catalog", "is_demo_data": True}


def list_allergens() -> AllergenList:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT number, name FROM allergen ORDER BY number")
        allergens = cursor.fetchall()
    return {"allergens": allergens, "count": len(allergens),
            "source": "demo_catalog", "is_demo_data": True}
