"""Streamable HTTP MCP service for the fictional pizza catalog."""

import hmac
import logging
import os

import psycopg
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from pizza_mcp import catalog
from pizza_mcp.models import AllergenCheck, AllergenList, IngredientList, PizzaDetail, PizzaList


logger = logging.getLogger(__name__)
mcp = MCPServer("AI Horizons pizza catalog",
                instructions="Return Czech answers grounded in demo records. Never infer an allergen-free guarantee.")


@mcp.tool()
def list_pizzas(category: str | None = None, query: str | None = None,
                available_only: bool = True, limit: int = 20) -> PizzaList:
    """Vypsat pizzy; filtrovat přesnou kategorií, částí názvu a dostupností."""
    return catalog.list_pizzas(category, query, available_only, limit)


@mcp.tool()
def get_pizza(pizza_id: str) -> PizzaDetail:
    """Přečíst cenu, aktuální recept a deklarované i nejisté alergenní profily pizzy."""
    return catalog.get_pizza(pizza_id)


@mcp.tool()
def check_allergen(pizza_id: str, allergen_number: int) -> AllergenCheck:
    """Zkontrolovat číslo alergenu 1–14 pro pizzu bez příslibu bezalergennosti."""
    return catalog.check_allergen(pizza_id, allergen_number)


@mcp.tool()
def list_ingredients() -> IngredientList:
    """Vypsat modelové suroviny včetně úplnosti jejich alergenního profilu."""
    return catalog.list_ingredients()


@mcp.tool()
def list_allergens() -> AllergenList:
    """Vypsat číslovaný seznam čtrnácti alergenů."""
    return catalog.list_allergens()


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> Response:
    if not os.environ.get("MCP_API_TOKEN") or not os.environ.get("DATABASE_URL"):
        return JSONResponse({"status": "unconfigured"}, status_code=503)
    try:
        with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3) as connection:
            connection.execute("SELECT 1")
    except psycopg.OperationalError:
        logger.exception("Catalog health check failed")
        return JSONResponse({"status": "database_unavailable"}, status_code=503)
    return JSONResponse({"status": "ok"})


class BearerProtectedApp:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] == "/healthz":
            await self.app(scope, receive, send)
            return
        expected = os.environ.get("MCP_API_TOKEN")
        headers = dict(scope["headers"])
        authorization = headers.get(b"authorization", b"")
        provided = authorization.removeprefix(b"Bearer ") if authorization.startswith(b"Bearer ") else b""
        if not expected or not hmac.compare_digest(provided, expected.encode("utf-8")):
            response = JSONResponse({"error": "Unauthorized"}, status_code=401,
                                    headers={"WWW-Authenticate": "Bearer"})
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


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
