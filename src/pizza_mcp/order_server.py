"""Independent read-only MCP endpoint for fictional order history."""

import logging
import os

import psycopg
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from pizza_mcp import orders
from pizza_mcp.order_models import Customers, Favorites, HistorySummary, OrderDetail, Orders
from pizza_mcp.server import BearerProtectedApp


logger = logging.getLogger(__name__)
mcp = MCPServer("AI Horizons order history",
                instructions="Use only fictional demo profiles. Answer in Czech; do not claim real authentication or payments.")


@mcp.tool()
def list_demo_customers() -> Customers:
    """Vypsat fiktivní profily, ze kterých si účastník dema vybere."""
    return orders.list_customers()


@mcp.tool()
def list_customer_orders(customer_id: str, status: str | None = None,
                         limit: int = 20) -> Orders:
    """Vypsat objednávky vybraného demo profilu, případně podle stavu."""
    return orders.list_orders(customer_id, status, limit)


@mcp.tool()
def get_customer_order(customer_id: str, order_id: str) -> OrderDetail:
    """Přečíst objednávku s historickými cenami jen v rámci vybraného profilu."""
    return orders.get_order(customer_id, order_id)


@mcp.tool()
def favorite_pizzas(customer_id: str, limit: int = 5) -> Favorites:
    """Seřadit pizzy podle kusů v doručených objednávkách demo profilu."""
    return orders.favorite_pizzas(customer_id, limit)


@mcp.tool()
def customer_order_summary(customer_id: str) -> HistorySummary:
    """Spočítat doručené, zrušené a celkové objednávky a hodnotu doručených."""
    return orders.order_summary(customer_id)


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> Response:
    if not os.environ.get("MCP_API_TOKEN") or not os.environ.get("DATABASE_URL"):
        return JSONResponse({"status": "unconfigured"}, status_code=503)
    try:
        with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3) as connection:
            connection.execute("SELECT 1 FROM demo_order LIMIT 1")
    except psycopg.Error:
        logger.exception("Order history health check failed")
        return JSONResponse({"status": "database_unavailable"}, status_code=503)
    return JSONResponse({"status": "ok"})


def create_app():
    hostname = os.environ.get("MCP_ALLOWED_HOST")
    security = None
    if hostname:
        if "/" in hostname or ":" in hostname:
            raise ValueError("MCP_ALLOWED_HOST must be a bare DNS hostname")
        security = TransportSecuritySettings(
            allowed_hosts=[hostname, f"{hostname}:*", "localhost:*", "127.0.0.1:*"],
            allowed_origins=[],
        )
    return BearerProtectedApp(mcp.streamable_http_app(
        stateless_http=True, json_response=True, transport_security=security,
    ))


app = create_app()
