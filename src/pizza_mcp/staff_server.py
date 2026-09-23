"""Separate staff-only MCP surface over fictional orders."""

import logging
import os

import psycopg
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from pizza_mcp import orders
from pizza_mcp.order_models import StaffOrderDetail, StaffOrders
from pizza_mcp.server import BearerProtectedApp


logger = logging.getLogger(__name__)
mcp = MCPServer(
    "AI Horizons staff orders",
    instructions="Fictional demo orders for staff only. Read-only. Answer in Czech.",
)


@mcp.tool()
def list_staff_orders(status: str | None = None, limit: int = 20) -> StaffOrders:
    """Vypsat objednávky všech fiktivních zákazníků, případně podle stavu."""
    return orders.list_staff_orders(status, limit)


@mcp.tool()
def get_staff_order(order_id: str) -> StaffOrderDetail:
    """Přečíst objednávku libovolného fiktivního zákazníka podle ID."""
    return orders.get_staff_order(order_id)


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> Response:
    if not os.environ.get("MCP_API_TOKEN") or not os.environ.get("DATABASE_URL"):
        return JSONResponse({"status": "unconfigured"}, status_code=503)
    try:
        with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3) as connection:
            connection.execute("SELECT 1 FROM demo_order LIMIT 1")
    except psycopg.Error:
        logger.exception("Staff order health check failed")
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
