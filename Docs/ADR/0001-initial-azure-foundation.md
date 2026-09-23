---
id: 0001
status: accepted
date: 2026-09-23
review_conditions:
  - signal: "Infrastructure is managed from multiple machines or checkouts"
    source: "infra/README.md and Terraform execution workflow"
    revisit_when: "Before the first apply outside this checkout"
  - signal: "Storage no longer requires access over the public endpoint"
    source: "Azure storage account network configuration"
    revisit_when: "Private connectivity is available"
---

# ADR-0001: Bootstrap Azure resources with Terraform and AzAPI

## Context

The first infrastructure increment requires a tagged resource group and a
document storage account in the active Azure subscription. A second session
needs a private container for demo pizza PDFs. More resources may be reconciled
from the portal later. No remote Terraform state backend exists.

## Options

- **AzAPI and local state:** Manage both resources with one provider and bootstrap
  immediately; state remains tied to this checkout until migrated.
- **AzureRM or portal-only deployment:** Familiar resource types, but contrary
  to the repository's AzAPI rule or without reproducible state.
- **Remote state now:** Safer for simultaneous checkouts, but adds a storage
  container and backend bootstrap outside this increment.

## Decision and rationale

Use Terraform with AzAPI in Sweden Central and preserve state locally for this
first, single-checkout increment. The resource group carries the requested
`Security Controls = ignore` tag and, with explicit approval, the separate
`SecurityControl = Ignore` tag required by the assigned modify policy. Create
the private `pizza-pdfs` container for the other session. The storage endpoint
permits public network traffic while requiring authenticated Entra data access,
HTTPS and TLS 1.2.

## Consequences

Only one checkout may apply at a time. Migrate the state to a locked remote
backend before parallel infrastructure work. Review and remove the temporary
policy exception and restrict storage networking when private access is ready;
this setup is not suitable for real customer data without further controls.
