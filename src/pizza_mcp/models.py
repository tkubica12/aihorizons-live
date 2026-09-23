"""MCP result contracts for the versioned demo catalog."""

from typing import Literal, TypedDict


class PizzaSummary(TypedDict):
    id: str
    name: str
    category: str
    description: str
    price_czk: int
    available: bool


class RecipeItem(TypedDict):
    id: str
    name: str
    grams: int
    allergen_profile_complete: bool
    profile_note: str


class Allergen(TypedDict):
    number: int
    name: str


class UncertainIngredient(TypedDict):
    ingredient: str
    note: str


class PizzaList(TypedDict):
    pizzas: list[PizzaSummary]
    count: int
    limit: int
    source: str
    is_demo_data: bool


class PizzaDetail(PizzaSummary):
    updated_at: str
    ingredients: list[RecipeItem]
    declared_allergens: list[Allergen]
    uncertain_ingredients: list[UncertainIngredient]
    source: str
    is_demo_data: bool
    safety_note: str


class AllergenCheck(TypedDict):
    pizza_id: str
    allergen_number: int
    allergen_name: str
    status: Literal["declared", "uncertain", "not_declared_in_demo_recipe"]
    uncertain_ingredients: list[UncertainIngredient]
    safety_note: str
    source: str
    is_demo_data: bool


class IngredientSummary(TypedDict):
    id: str
    name: str
    allergen_profile_complete: bool
    profile_note: str


class IngredientList(TypedDict):
    ingredients: list[IngredientSummary]
    count: int
    source: str
    is_demo_data: bool


class AllergenList(TypedDict):
    allergens: list[Allergen]
    count: int
    source: str
    is_demo_data: bool
