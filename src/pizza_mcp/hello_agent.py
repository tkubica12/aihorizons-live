"""Externally hosted LangGraph hello demo with Foundry-linked traces."""

import hmac
import os

from azure.monitor.opentelemetry import configure_azure_monitor
from langgraph.graph import END, START, StateGraph
from opentelemetry import trace
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from typing_extensions import TypedDict


AGENT_NAME = "pizza-hello-external"


class HelloState(TypedDict):
    message: str
    response: str


def greet(state: HelloState) -> dict[str, str]:
    return {"response": "Ahoj! Jsem externí demo agent běžící mimo Foundry."}


builder = StateGraph(HelloState)
builder.add_node("greet", greet)
builder.add_edge(START, "greet")
builder.add_edge("greet", END)
graph = builder.compile()


def configure_telemetry() -> None:
    configure_azure_monitor(
        connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"],
        instrumentation_options={"httpx": {"enabled": False}, "requests": {"enabled": False}},
    )


async def healthz(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def chat(request: Request) -> JSONResponse:
    token = os.environ["HELLO_API_TOKEN"]
    authorization = request.headers.get("authorization", "")
    if not hmac.compare_digest(authorization, f"Bearer {token}"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    body = await request.json()
    if not isinstance(body, dict) or not isinstance(body.get("message"), str):
        return JSONResponse({"error": "message must be a string"}, status_code=400)
    if not body["message"].strip() or len(body["message"]) > 2000:
        return JSONResponse({"error": "message must contain 1-2000 characters"}, status_code=400)
    with trace.get_tracer(__name__).start_as_current_span("invoke_agent") as span:
        span.set_attribute("gen_ai.agent.id", AGENT_NAME)
        span.set_attribute("gen_ai.agent.name", AGENT_NAME)
        result = await graph.ainvoke({"message": body["message"], "response": ""})
    return JSONResponse({"response": result["response"]})


app = Starlette(routes=[
    Route("/healthz", healthz),
    Route("/chat", chat, methods=["POST"]),
])


if __name__ == "__main__":
    if not os.environ.get("HELLO_API_TOKEN"):
        raise RuntimeError("HELLO_API_TOKEN is required")
    configure_telemetry()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
