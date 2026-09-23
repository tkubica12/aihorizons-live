---
id: 0005
status: accepted
date: 2026-09-23
review_conditions:
  - signal: "A Teams channel and real employee authentication are required"
    source: "Docs/PRD.md and deployed staff identity architecture"
    revisit_when: "Demo transitions from fictional read-only orders to staff writes or real customer data"
  - signal: "MCP client and LangChain adapters support a compatible SDK version"
    source: "pyproject.toml, uv.lock and hosted toolbox integration tests"
    revisit_when: "A maintained adapter supports the project's MCP SDK without split environments"
---

# ADR-0005: Separate staff and external LangGraph runtimes

## Context

The customer order MCP scopes queries by selected fictional profile. Staff need
cross-customer reads for triage, but exposing those tools on the customer MCP
or toolbox would defeat that demo boundary. Foundry hosts the coded staff
agent; a second agent demonstrates management and telemetry registration
without Foundry compute. The existing customer assistant is portal-defined.

## Options

- **Add staff tools to the customer MCP/toolbox:** fewer components, but any
  customer agent could read all fictional orders.
- **Separate staff MCP and toolbox, hosted LangGraph staff agent:** maintains
  access separation, uses Foundry identity and native hosting; adds a service
  and credential. The external hello agent runs independently in Container Apps.
- **Run both agents in Container Apps:** simpler hosting but does not demonstrate
  Foundry hosted agents.

## Decision and rationale

Use a separate staff MCP with SELECT-only database access and a distinct
credential. Copy read-only catalog/knowledge tools to a staff-only Foundry
toolbox. The Python LangGraph hosted agent calls the toolbox over authenticated
MCP; Foundry runs its container and Responses endpoint. Register the
independent Container Apps hello graph as `external` and match its
`gen_ai.agent.id` to the registration. Use AzAPI/Terraform for Azure resources
and an explicit SDK script for Foundry data-plane versions.

The available LangChain MCP adapter imports an API removed by this project's
MCP 2.2 SDK. A small bridge using the MCP SDK's public Streamable HTTP
`ClientSession`, with fresh Entra tokens, exposes toolbox tools to LangGraph
without downgrading the customer MCP server. The current Foundry toolbox gateway
omits `$defs` from some nested MCP output schemas. For catalog and staff tools
the bridge validates returned structured content against the original typed
Python contracts instead of the gateway's incomplete copy; other self-contained
schemas retain JSON Schema validation. Remove this compatibility path if the
gateway starts returning complete output schemas.

## Consequences

The read-only demo is **not** an employee identity/authorization solution;
Teams, preparation writes, complaints, dispatch, approvals and evaluations
remain future milestones. Do not connect real orders or expose the staff
credential to the customer service. Foundry external registration adds
observability only: it neither secures nor operates the Container App. The
external preview has no production SLA. Tool approval must be implemented in
code before adding any `require_approval: always` tool; the current toolbox
uses read-only tools with `never`. Rotate secrets and review audit access
before changing the data classification.
