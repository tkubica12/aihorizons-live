"""Bounded queries over fictional, customer-scoped order records."""

import logging
import os

import psycopg
from mcp.server.mcpserver.exceptions import ToolError
from psycopg.rows import dict_row

from pizza_mcp.order_models import Customers, Favorites, HistorySummary, OrderDetail, Orders
from pizza_mcp.order_seed import STATUSES


logger = logging.getLogger(__name__)


def connect() -> psycopg.Connection:
    try:
        return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row, connect_timeout=5)
    except psycopg.OperationalError as exc:
        logger.exception("Order database connection failed")
        raise ToolError("Databáze objednávek není dostupná.") from exc


def _customer(cursor: psycopg.Cursor, customer_id: str) -> None:
    if not customer_id.strip():
        raise ToolError("Zvolte ID fiktivního zákazníka.")
    cursor.execute("SELECT 1 FROM demo_customer WHERE id = %s", (customer_id,))
    if cursor.fetchone() is None:
        raise ToolError(f"Fiktivní zákazník {customer_id!r} neexistuje.")


def list_customers() -> Customers:
    """List selectable fictional profiles; this is not customer authentication."""
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT id, display_name FROM demo_customer ORDER BY display_name")
        customers = cursor.fetchall()
    return {"customers": customers, "count": len(customers), "is_demo_data": True}


def list_orders(customer_id: str, status: str | None = None, limit: int = 20) -> Orders:
    if not 1 <= limit <= 50:
        raise ToolError("Limit musí být mezi 1 a 50.")
    if status is not None and status not in STATUSES:
        raise ToolError(f"Neznámý stav objednávky: {status!r}.")
    with connect() as connection, connection.cursor() as cursor:
        _customer(cursor, customer_id)
        statement = (
            "SELECT id, placed_at::text AS placed_at, status, total_czk "
            "FROM demo_order WHERE customer_id = %s"
        )
        params = [customer_id]
        if status is not None:
            statement += " AND status = %s"
            params.append(status)
        statement += " ORDER BY placed_at DESC, id DESC LIMIT %s"
        params.append(limit)
        cursor.execute(statement, params)
        rows = cursor.fetchall()
    return {"customer_id": customer_id, "orders": rows, "count": len(rows),
            "limit": limit, "is_demo_data": True}


def get_order(customer_id: str, order_id: str) -> OrderDetail:
    with connect() as connection, connection.cursor() as cursor:
        _customer(cursor, customer_id)
        cursor.execute(
            """SELECT id, customer_id, placed_at::text AS placed_at, status, total_czk
               FROM demo_order WHERE id = %s AND customer_id = %s""",
            (order_id, customer_id),
        )
        order = cursor.fetchone()
        if order is None:
            raise ToolError("Objednávka pro zvolený demo profil neexistuje.")
        cursor.execute(
            """SELECT pizza_id, pizza_name, quantity, unit_price_czk,
                      quantity * unit_price_czk AS line_total_czk
               FROM demo_order_item WHERE order_id = %s ORDER BY pizza_id""",
            (order_id,),
        )
        items = cursor.fetchall()
    return {**order, "items": items, "is_demo_data": True}


def favorite_pizzas(customer_id: str, limit: int = 5) -> Favorites:
    if not 1 <= limit <= 20:
        raise ToolError("Limit musí být mezi 1 a 20.")
    with connect() as connection, connection.cursor() as cursor:
        _customer(cursor, customer_id)
        cursor.execute(
            """SELECT i.pizza_id, i.pizza_name,
                      sum(i.quantity)::integer AS quantity,
                      count(*)::integer AS order_count
               FROM demo_order o JOIN demo_order_item i ON i.order_id = o.id
               WHERE o.customer_id = %s AND o.status = 'delivered'
               GROUP BY i.pizza_id, i.pizza_name
               ORDER BY quantity DESC, i.pizza_name, i.pizza_id LIMIT %s""",
            (customer_id, limit),
        )
        pizzas = cursor.fetchall()
    return {"customer_id": customer_id, "pizzas": pizzas, "limit": limit,
            "basis": "delivered_orders_only", "is_demo_data": True}


def order_summary(customer_id: str) -> HistorySummary:
    with connect() as connection, connection.cursor() as cursor:
        _customer(cursor, customer_id)
        cursor.execute(
            """SELECT count(*)::integer AS order_count,
                      count(*) FILTER (WHERE status = 'delivered')::integer AS delivered_count,
                      count(*) FILTER (WHERE status = 'cancelled')::integer AS cancelled_count,
                      coalesce(sum(total_czk) FILTER (WHERE status = 'delivered'), 0)::integer
                          AS delivered_total_czk,
                      min(placed_at)::text AS first_order_at,
                      max(placed_at)::text AS last_order_at
               FROM demo_order WHERE customer_id = %s""",
            (customer_id,),
        )
        summary = cursor.fetchone()
    return {"customer_id": customer_id, **summary, "is_demo_data": True}
