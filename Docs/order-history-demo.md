# Fictional order-history MCP

This separate, read-only milestone-2 example contains three fictional demo
profiles and six historical orders. It is **not** customer authentication,
payment history or a real order-creation service. It excludes cancelled and
unfinished orders from delivered value and favorite-pizza rankings.
The temporarily approved HorizonDB "Allow Azure Services" rule covers **all**
Azure subscriptions, not just these Container Apps; do not store real customer
data. See `Docs/catalog-demo.md` for the network exception and its removal.

Run the catalog seed first. With a privileged `DATABASE_URL` and network
access to HorizonDB, run `uv run --frozen python -m pizza_mcp.order_seed`.
The fixture is `sample-data/order-history.json`; historical item names and
unit prices are captured from the seeded catalog on initial insert. Repeating
the seed leaves existing orders untouched, preserving later status changes.
The following database counts should then be 3, 6 and 7:

```sql
SELECT count(*) FROM demo_customer;
SELECT count(*) FROM demo_order;
SELECT count(*) FROM demo_order_item;
```

Deploy the same versioned image as a **separate** Container App with command
`uvicorn pizza_mcp.order_server:app --host 0.0.0.0 --port 8000 --proxy-headers`.
Give its runtime connection SELECT on the three `demo_*` tables only. Set
`DATABASE_URL`, `MCP_API_TOKEN` via Container App secrets and `MCP_ALLOWED_HOST`
to the new app's exact hostname. The five tools are `list_demo_customers`,
`list_customer_orders`, `get_customer_order`, `favorite_pizzas` and
`customer_order_summary`. The first lists selectable profiles; callers must
specify a selected `customer_id` for all other tools. `get_customer_order`
requires both customer and order ID, preventing accidental cross-profile
lookup in this demo, **not** malicious access without authentication.

The order endpoint is `/mcp` and health endpoint `/healthz`. Do not expose this
service as a real customer account API until verified authentication and
authorization are implemented.

From a local computer set `ORDER_MCP_URL` to the deployed HTTPS base URL and
`MCP_API_TOKEN` in the process environment, then run `uv run --frozen python
scripts/verify_orders_mcp.py`. This checks the real database-backed tools,
seeded record counts, historic totals and a cross-profile not-found result.
The generated tool contract is `Docs/Contracts/order-history.mcp.json`;
regenerate it with `uv run --frozen python scripts/export_mcp_contract.py`.
