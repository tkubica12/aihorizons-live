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
