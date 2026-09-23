"""Typed results of the fictional order-history MCP."""

from typing import TypedDict


class Customer(TypedDict):
    id: str
    display_name: str


class Customers(TypedDict):
    customers: list[Customer]
    count: int
    is_demo_data: bool


class OrderSummary(TypedDict):
    id: str
    placed_at: str
    status: str
    total_czk: int


class Orders(TypedDict):
    customer_id: str
    orders: list[OrderSummary]
    count: int
    limit: int
    is_demo_data: bool


class OrderItem(TypedDict):
    pizza_id: str
    pizza_name: str
    quantity: int
    unit_price_czk: int
    line_total_czk: int


class OrderDetail(OrderSummary):
    customer_id: str
    items: list[OrderItem]
    is_demo_data: bool


class Favorite(TypedDict):
    pizza_id: str
    pizza_name: str
    quantity: int
    order_count: int


class Favorites(TypedDict):
    customer_id: str
    pizzas: list[Favorite]
    limit: int
    basis: str
    is_demo_data: bool


class HistorySummary(TypedDict):
    customer_id: str
    order_count: int
    delivered_count: int
    cancelled_count: int
    delivered_total_czk: int
    first_order_at: str | None
    last_order_at: str | None
    is_demo_data: bool
