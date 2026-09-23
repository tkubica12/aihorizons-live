# Architecture

The initial Azure footprint is managed in `infra/` with Terraform and AzAPI:
`RG-AI-Horizons` in Sweden Central contains one StorageV2 account and a private
`pizza-pdfs` blob container for demo documents. See `infra/README.md` for
deployment and state ownership. Application components, data flows and further
resources will be defined as milestones are implemented. The existing Foundry
account, project and model deployment are reconciled in `infra/foundry.tf`.

The customer demo runs locally as a Starlette app (`pizza_mcp.web`). A static
Czech chat page calls `POST /api/chat` on the same origin. The Python backend
uses the local operator's Azure identity to reach the existing named Foundry
agent through the project's Conversations/Responses API; the browser never
receives Azure credentials. A conversation ID is kept in browser session
storage to maintain context until "New chat" is selected. No customer login or
profile isolation is implemented: bind the server to loopback only, and do not
use the demo with real customer data or publish it without access controls.

Foundry project data-plane definitions are separately snapshotted under
`foundry/`: prompt-agent versions, evaluation JSONL datasets, custom evaluators,
evaluation recipes, historical run summaries, toolbox versions, memory-store
settings, and a credential-free project connection inventory. These are not
managed by Terraform. See [ADR-0004](ADR/0004-foundry-data-plane-assets.md) and
[`foundry/README.md`](../foundry/README.md) for the explicit export and
drift-checked restore workflow.

## Catalog milestone

Azure HorizonDB (PostgreSQL 17, Sweden Central) holds a relational, fictional
catalog: `pizza` -> `pizza_ingredient` -> `ingredient` ->
`ingredient_allergen` -> `allergen`. Database migration and deterministic
fixtures live in `database/` and `sample-data/catalog.json`; the editorial PDFs
remain independent and are not authoritative allergen declarations.

An Azure Container App runs `pizza_mcp.server` as a single-replica, read-only
Streamable HTTP MCP endpoint at `/mcp`. HTTPS ingress requires a demo bearer
token. The database runtime role has SELECT privileges only; a separate seed
role owns migrations and catalog writes. `/healthz` is public but reveals only
service/database availability. The project Canvas extension proxies approved
MCP calls from a loopback UI to the Azure endpoint and never saves the token.

See [ADR-0002](ADR/0002-catalog-and-mcp.md) and the generated
[`pizza-catalog.mcp.json`](Contracts/pizza-catalog.mcp.json) tool contract.

## Order-history example

Milestone 2 adds a separate read-only MCP process over three `demo_*` tables
in the same HorizonDB cluster. Fictional profiles, orders and immutable
historical line-item prices are seeded after the catalog; queries scope orders
to an explicitly selected profile. This is a demo control, not verified
authentication. Favorites and delivered totals omit unfinished and cancelled
orders. See [ADR-0003](ADR/0003-order-history-mcp.md), the
[`order-history.mcp.json`](Contracts/order-history.mcp.json) contract and
[setup notes](order-history-demo.md). No transactional ordering or dispatch
capability is implemented by this second MCP.

## Coded staff agent and external demo

`pizza_mcp.staff_server` runs as a third, read-only MCP process in Container Apps.
Unlike the customer-scoped order server, it can query all fictional customer
orders, but it has a **different bearer token and connection** and uses the same
database SELECT-only role. The `pizza-staff-tools` Foundry toolbox copies the
catalog and knowledge-base tool references and adds only this staff MCP. The
customer toolbox remains unchanged.

`pizza_mcp.staff_agent` is a Python LangGraph ReAct graph in a Foundry **hosted**
container, serving the Responses 2.0 protocol. It calls the staff toolbox's
consumer MCP endpoint using its Foundry identity, and the existing Foundry
model using Entra tokens. The Foundry platform owns ingress, agent identity,
conversation storage and Application Insights connection. The agent currently
has no Teams adapter and no state-changing tools.

`pizza_mcp.hello_agent` is a separate LangGraph graph in Azure Container Apps,
not a Foundry hosted agent. It exposes a token-protected `/chat` demo route,
exports OpenTelemetry traces to the Foundry project's Application Insights,
and emits `gen_ai.agent.id=pizza-hello-external`. An **external** Foundry agent
record associates these traces with its name. Foundry registration does not
host, authenticate, or proxy this Container App.

See [ADR-0005](ADR/0005-coded-agents.md) and [deployment notes](agents-demo.md).
