# Staff hosted and external LangGraph agents

The staff agent `pizza-staff-langgraph` is a **Foundry hosted** Python LangGraph
container. Its staff-only toolbox includes catalog, KB and cross-customer
fictional orders. The external `pizza-hello-external` runs in Azure Container
Apps and is only registered in Foundry for Application Insights traces.

Deployment (explicit operator workflow from the repository root):

1. Sign in to Azure CLI with access to the `aihorizons` Foundry project,
   registry and Key Vault. Keep the existing `infra/terraform.tfstate`; use
   the project's approved Microsoft PyPI feed (`uv sync --frozen --extra agents
   --extra dev`). Ensure Key Vault holds distinct random secrets named
   `mcp-staff-api-token` and `external-hello-api-token`, not reused customer
   credentials. The existing `orderdb-runtime-url` is SELECT-only.
2. Build three images in `aihorizons673af34dacr` from `Dockerfile`
   (staff MCP), `Dockerfile.hosted` and `Dockerfile.external` with
   `az acr build -r aihorizons673af34dacr -f <Dockerfile> -t <unique-tag> .`.
   Resolve their immutable `sha256:` digests; never deploy `latest`.
3. Plan and apply Terraform in `infra/` with `staff_mcp_image` and
   `external_agent_image` set to the digest references. Retrieve
   `horizondb-admin-password` into `TF_VAR_horizondb_admin_password` in the
   shell, without printing it. Review the full plan for unexpected changes.
   Terraform gives the Foundry project identity AcrPull and creates only the
   two Container Apps. Its output gives the staff MCP and external chat URLs.
4. Run `uv run --no-sync --extra agents python scripts/deploy_agents.py
   toolbox`. This registers `pizza-staff-orders-mcp` with a Key Vault-backed
   token in Foundry's project connection and creates `pizza-staff-tools`;
   it never changes the customer toolbox. Run `... deploy_agents.py hosted
   --image <hosted-image@sha256:digest>` to create a new Foundry hosted version.
   Run `... deploy_agents.py external` to register the existing ACA process
   as an external agent with a matching OpenTelemetry ID. Data-plane changes
   are versioned explicitly. Snapshot the new staff toolbox and connection
   inventory with `scripts/foundry_assets.py snapshot --overwrite` after
   reviewing the diff. The two coded agents themselves are intentionally
   excluded from the prompt-agent snapshot: `deploy_agents.py` and the
   container images are their source of truth.
5. Verify `/healthz` on both Container Apps. From an authorized Azure
   identity, call the hosted agent through
   `AIProjectClient(...).get_openai_client(agent_name="pizza-staff-langgraph")`
   and `responses.create(input="Vypiš poslední objednávky všech zákazníků.")`.
   It should return the six seeded orders across Anna, Boris and Cyril.
   Call the ACA `/chat` route with
   `Authorization: Bearer <external-hello-api-token>` and
   `{"message":"ahoj"}`; then inspect the external agent's traces in Foundry
   or Application Insights for `gen_ai.agent.id=pizza-hello-external`.

**Security limits:** The staff MCP is token-protected and read-only, but it
does not verify individual employees. The hosted gateway authenticates
callers, not their employment role: restrict project/agent permissions to demo
staff until a Teams authentication/authorization layer exists. Do not use
real personal data. The hello service authenticates calls itself because
external Foundry registration does not provide ingress security. Avoid putting
customer text or tokens in telemetry. Application Insights traces can be
delayed; a healthy service alone does not prove that traces have arrived.

Official references: [Hosted agent container and Python SDK](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent),
[hosted toolbox MCP](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/use-toolbox-hosted-agent),
[external agent registration and tracing](https://learn.microsoft.com/azure/foundry/agents/how-to/register-external-agent).
