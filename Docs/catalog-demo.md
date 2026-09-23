# Pizza catalog demo

Milestone 1 includes 12 fictional pizzas, 27 ingredients and all 14 numbered
allergens. `sample-data/catalog.json` is the seeded business record; prices,
availability and recipe weights are illustrative. `sample-data/pizza-pdfs/`
contains separate editorial sheets, not an official allergen declaration.
Compound ingredients without a verified supplier label are marked incomplete.
The assistant must not infer "free from" from an absent record.

## Local and Azure setup

The local project uses `uv` and the Microsoft package feed configured in
`pyproject.toml`. Run `uv sync --extra dev --frozen`; tests are `uv run --frozen
pytest -q`. The generated MCP tool contract can be refreshed with `uv run
--frozen python scripts/export_mcp_contract.py`.
In the container, `PIZZA_DATA_ROOT=/app` points both seed modules at the
fixture and SQL files copied outside the non-editable Python wheel. Set this
variable to the directory containing `database/` and `sample-data/` if
running an installed wheel outside the provided image.

Infrastructure is owned in `infra/` by the Azure infrastructure session.
For the fictional demo only, the owner approved HorizonDB's broad
**Allow Azure Services** firewall rule while the private endpoint subscription
feature is pending. This permits network connections from **all Azure
subscriptions**, not only this project's resources; PostgreSQL credentials,
TLS and read-only roles remain mandatory. Remove the broad rule and migrate
to private connectivity when the feature is registered. Never seed real
customer records while the rule exists.
Use an elevated *seed-only* PostgreSQL connection string in `DATABASE_URL` and
run `uv run --frozen python -m pizza_mcp.seed` from a client with database
network access (for a private database, a one-off Container Apps job in the
connected VNet). Seeding creates five tables and upserts the 12 pizzas
atomically; repeat runs update fixture-owned recipes.
Verify the database with:

```sql
SELECT count(*) FROM pizza;             -- 12
SELECT count(*) FROM ingredient;        -- 27
SELECT count(*) FROM allergen;          -- 14
SELECT count(*) FROM pizza_ingredient;  -- 71
```

Grant a different runtime identity SELECT on those five tables only. Store its
`DATABASE_URL` and a randomly generated `MCP_API_TOKEN` in Azure Container App
secrets, never in repo files or image layers. The container listens on port
8000; set `MCP_ALLOWED_HOST` to its exact public Container App FQDN without a
scheme. `/healthz` returns `{"status":"ok"}` only when the database is reachable.
Point an MCP client at `https://<app-fqdn>/mcp`, sending the bearer token in
the `Authorization` header. The service offers `list_pizzas`, `get_pizza`,
`check_allergen`, `list_ingredients` and `list_allergens` (read-only).
For a reproducible end-to-end check from the local computer, set `MCP_URL`
to the HTTPS Container App base URL and `MCP_API_TOKEN` in the shell environment
(without writing them to files), then run `uv run --frozen python
scripts/verify_mcp.py`. It checks the health endpoint, tool discovery and
five real tool calls against seeded records.

Open the project Canvas **Pizza catalog / MCP** for a manual test. Enter the
Container App URL and token (the token is held only in the open panel), click
**Ověřit službu**, then **Načíst MCP nástroje** and **Vyhledat pizzy**.
Select a pizza to inspect its recipe and allergen uncertainty, or call a tool
with arbitrary JSON arguments and inspect the protocol response. Do not paste
the token into screenshots, shared logs or issue descriptions.

The demo is not a production food-safety service. The declared ingredients
and allergens are fictional, supplier-specific products can add allergens,
and cross-contact is not modeled.
