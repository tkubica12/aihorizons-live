"""Local customer chat backed by the existing Microsoft Foundry agent."""

import asyncio
import logging
import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route


logger = logging.getLogger(__name__)
STATIC = Path(__file__).parent / "static"
PROJECT_ENDPOINT = "https://aihorizons-resource.services.ai.azure.com/api/projects/aihorizons"
AGENT_NAME = "nejlepsi-ai-pizza-na-pankraci"


def ask_agent(message: str, conversation_id: str | None) -> tuple[str, str]:
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT", PROJECT_ENDPOINT),
            credential=credential,
        ) as project,
        project.get_openai_client(agent_name=os.environ.get("FOUNDRY_AGENT_NAME", AGENT_NAME)) as client,
    ):
        if conversation_id is None:
            conversation_id = client.conversations.create().id
        response = client.responses.create(conversation=conversation_id, input=message)
        if not response.output_text or not response.output_text.strip():
            raise ValueError("Foundry returned no text response")
        return response.output_text, conversation_id


async def chat(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse({"error": "Neplatný JSON požadavek."}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "Neplatný požadavek."}, status_code=400)
    message = payload.get("message")
    conversation_id = payload.get("conversation_id")
    if not isinstance(message, str) or not message.strip() or len(message) > 4000:
        return JSONResponse({"error": "Zpráva musí mít 1 až 4000 znaků."}, status_code=400)
    if conversation_id is not None and (
        not isinstance(conversation_id, str) or not conversation_id.startswith("conv_")
        or len(conversation_id) > 128
    ):
        return JSONResponse({"error": "Neplatná konverzace."}, status_code=400)
    try:
        answer, conversation_id = await asyncio.to_thread(ask_agent, message.strip(), conversation_id)
    except Exception:
        logger.exception("Foundry agent request failed")
        return JSONResponse(
            {"error": "Spojení s pizzovým asistentem se nezdařilo. Zkuste zprávu odeslat znovu."},
            status_code=502,
        )
    return JSONResponse({"answer": answer, "conversation_id": conversation_id})


async def index(request: Request) -> FileResponse:
    return FileResponse(STATIC / "index.html")


async def asset(request: Request) -> FileResponse:
    name = request.path_params["name"]
    if name not in {"style.css", "app.js", "pizza.svg"}:
        return JSONResponse({"error": "Nenalezeno."}, status_code=404)
    return FileResponse(STATIC / name)


app = Starlette(routes=[
    Route("/", index),
    Route("/api/chat", chat, methods=["POST"]),
    Route("/static/{name}", asset),
])
