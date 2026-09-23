"""Seed deterministic fictional order history without replacing live orders."""

import json
import os
from datetime import datetime
from pathlib import Path

import psycopg

from pizza_mcp.seed import ROOT, load_fixture


FIXTURE = ROOT / "sample-data" / "order-history.json"
SCHEMA = ROOT / "database" / "002_order_history.sql"
STATUSES = {"confirmed", "preparing", "ready", "dispatched", "delivered", "cancelled"}


def load_orders(path: Path = FIXTURE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    customers = [customer["id"] for customer in data["customers"]]
    order_ids = [order["id"] for order in data["orders"]]
    pizza_ids = {pizza["id"] for pizza in load_fixture()["pizzas"]}
    if len(customers) != len(set(customers)) or len(order_ids) != len(set(order_ids)):
        raise ValueError("Duplicate demo customer or order ID")
    for order in data["orders"]:
        if order["customer_id"] not in customers or order["status"] not in STATUSES:
            raise ValueError(f"Unknown customer or status in {order['id']}")
        if datetime.fromisoformat(order["placed_at"].replace("Z", "+00:00")).utcoffset() is None:
            raise ValueError(f"Timestamp must have a timezone in {order['id']}")
        ids = [item["pizza_id"] for item in order["items"]]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError(f"Missing or duplicate pizza items in {order['id']}")
        if any(item["pizza_id"] not in pizza_ids or type(item["quantity"]) is not int
               or item["quantity"] <= 0 for item in order["items"]):
            raise ValueError(f"Invalid pizza item in {order['id']}")
    return data


def seed(connection: psycopg.Connection, data: dict) -> None:
    with connection.transaction(), connection.cursor() as cursor:
        cursor.execute(SCHEMA.read_text(encoding="utf-8"))
        for customer in data["customers"]:
            cursor.execute(
                """INSERT INTO demo_customer (id, display_name) VALUES (%s, %s)
                   ON CONFLICT (id) DO UPDATE SET display_name = EXCLUDED.display_name""",
                (customer["id"], customer["display_name"]),
            )
        for order in data["orders"]:
            ids = [item["pizza_id"] for item in order["items"]]
            cursor.execute(
                "SELECT id, name, price_czk FROM pizza WHERE id = ANY(%s)", (ids,)
            )
            pizzas = {pizza[0]: pizza for pizza in cursor.fetchall()}
            if set(ids) != pizzas.keys():
                raise ValueError(f"Catalog is missing pizzas for {order['id']}")
            total = sum(pizzas[item["pizza_id"]][2] * item["quantity"]
                        for item in order["items"])
            cursor.execute(
                """INSERT INTO demo_order (id, customer_id, placed_at, status, total_czk)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO NOTHING""",
                (order["id"], order["customer_id"], order["placed_at"], order["status"], total),
            )
            if cursor.rowcount == 0:
                continue
            for item in order["items"]:
                pizza = pizzas[item["pizza_id"]]
                cursor.execute(
                    """INSERT INTO demo_order_item
                       (order_id, pizza_id, pizza_name, quantity, unit_price_czk)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (order["id"], pizza[0], pizza[1], item["quantity"], pizza[2]),
                )


def main() -> None:
    data = load_orders()
    with psycopg.connect(os.environ["DATABASE_URL"]) as connection:
        seed(connection, data)
    print(f"Seeded {len(data['customers'])} demo customers and {len(data['orders'])} demo orders.")


if __name__ == "__main__":
    main()
