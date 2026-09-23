# Initial Azure infrastructure

Run `terraform init`, `terraform plan` and `terraform apply` from `infra/` after
signing in with `az login` and selecting subscription
`673af34d-6b28-41dc-bc7b-f507418045e6`. Terraform uses the AzAPI provider to
manage the `RG-AI-Horizons` resource group and the
`aihorizons673af34ddocs` document storage account in Sweden Central.

The resource group has the requested exact tag `Security Controls = ignore` and
also `SecurityControl = Ignore`, the *separate* tag recognized by the assigned
Azure Policy to allow the public storage endpoint. This temporary exception must
be reviewed and removed when private connectivity is available. Anonymous blob
access and Shared Key authorization are disabled: data access requires an Entra
identity with an appropriate Storage Blob Data role, over HTTPS/TLS 1.2. The
private `pizza-pdfs` container holds demo PDFs; no documents are created here.
For an identity with Storage Blob Data Contributor/Owner, upload with
`az storage blob upload --account-name aihorizons673af34ddocs --container-name pizza-pdfs --name <file.pdf> --file <path> --auth-mode login`.

State is currently local in `infra/terraform.tfstate`, which is ignored by Git
and **must be preserved**. Run Terraform against this state from the same
checkout; do not run `apply` concurrently from another session or worktree.
Move the state into a locked remote backend before managing this infrastructure
from multiple machines or independent checkouts. Keep `.terraform.lock.hcl` in
version control, but never commit state or secret variable files. For
portal-created resources, add an AzAPI declaration, import the Azure resource ID
into this state, then ensure `terraform plan` has no unexpected drift before
applying further changes.

The portal-created Foundry account `aihorizons-resource`, project `aihorizons`
and `gpt-6-sol` model deployment are declared in `foundry.tf` and imported into
this state. Their current model version, GlobalStandard capacity (477), SKU,
account network settings and managed identities are reflected in Terraform;
each resource has `prevent_destroy`. Before changing a property in the portal,
reconcile its value here and check `terraform plan` for unexpected drift.

HorizonDB `hdb-aihorizons` (PostgreSQL 17, two vCores, one replica) uses the
ephemeral `horizondb_admin_password` Terraform variable and the provider's
write-only `sensitive_body`. For each plan/apply, load the value from the
`horizondb-admin-password` secret in `kvaihorizons673af34d` into
`TF_VAR_horizondb_admin_password` in the process environment; never put it in
a `.tfvars` file, command argument, log, or Terraform state. The cluster was
bootstrapped without public firewall rules. `network.tf` declares a dedicated VNet, a
delegated `/27` Container Apps subnet, a separate private endpoint subnet,
`DefaultPool` HorizonDB private link, and the Azure-provided
`privatelink.horizondb.azure.com` DNS zone. The external Container Apps
environment is VNet-integrated so it can use the private DB endpoint when
available while its HTTPS ingress remains public. The original empty
`cae-aihorizons` environment remains intact until the replacement is proven.

`identity.tf` grants the user-assigned `id-pizza-mcp` only AcrPull and Key Vault
Secrets User at the respective resource scopes. The manual job
`job-pizza-catalog-bootstrap` seeds the fictional catalog and creates a
SELECT-only `pizza_reader` PostgreSQL role. It reads its two passwords by
managed-identity Key Vault reference; executing it requires an explicit
`az containerapp job start`, and merely applying Terraform does not run it.
Only run the job after its configured database network path is healthy. The
`Microsoft.Network/AllowPrivateEndpoints` subscription feature was `Pending`
on 2026-09-23, blocking the private endpoint. For this **fictional demo only**,
the explicitly approved default `database_network_mode=azure_services` creates
one HorizonDB firewall rule with `0.0.0.0` at both ends. This is **not** an
AI Horizons-only or tenant-only exception: it permits connections from every
Azure subscription, including other tenants, subject to TLS and valid
database credentials. Do not use real customer data. Keep the admin credential
private and the two runtime roles SELECT-only on their respective tables.
Once the feature becomes `Registered`, re-register the `Microsoft.Network`
provider to propagate it, plan and apply with
`-var database_network_mode=private_endpoint`, verify private DNS and
connectivity, and confirm the `allow-azure-services-demo` rule was deleted.
Use the same mode for every plan/apply until that deliberate transition;
do not leave the wide rule in place afterward.

`catalog_app.tf` and `order_service.tf` declare two separate authenticated
HTTPS MCP apps with at most one replica each. The second manual job must run
*after* the catalog job succeeds, because its fixture references seeded
pizzas; it creates `orders_reader` with SELECT only on the three `demo_*`
tables. The apps reference `horizondb-runtime-url`, `orderdb-runtime-url`,
`mcp-api-token`, and `mcp-orders-api-token` Key Vault secrets (the first two
are PostgreSQL URLs with separate read-only users). These secrets and
`orderdb-runtime-password` already exist in the vault; neither database
reader role exists on a fresh deployment until its bootstrap job succeeds. Never put secret values
in plan, state, repo, logs, or messages. A declared job resource does not
imply its seed has run; verify the execution and table counts before starting
the apps.

The 2026-09-23 demo bootstrap executions completed successfully: catalog
12 pizzas / 27 ingredients / 14 allergens / 71 pizza-ingredient rows, then
orders 3 demo customers / 6 orders / 7 order items. The immutable image
is `pizza-mcp@sha256:7bc829bf915eb3c32fcb4f27b43c6d15876cd0c079f2a033efb33e913037d9db`.
The HTTPS endpoints are available via `terraform output catalog_mcp_url`
and `terraform output orders_mcp_url`. Both `/healthz` endpoints return 200;
`/mcp` requires the respective distinct bearer token from Key Vault.

An unapproved fallback is declared in `static_egress_fallback.tf`, disabled
by default. `terraform plan -var database_network_mode=static_egress` previews
a Standard NAT Gateway and one Standard static public IP on the ACA subnet,
plus a HorizonDB firewall rule whose start and end addresses equal that one
IP. **Do not apply this mode without separate approval** of the increased
cost and public database exposure; it is not an Azure-wide allow rule.
As of 2026-09-23 the Azure Retail Prices API quotes USD 0.045/hour for the
Standard NAT Gateway, USD 0.005/hour for the static IPv4 address, and USD
0.045/GB NAT data processing: about USD 36.50 for a 730-hour month plus
traffic, excluding tax, discounts, and existing environment charges.
