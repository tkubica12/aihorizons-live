---
id: 0002
status: accepted
date: 2026-09-23
review_conditions:
  - signal: "Orders or staff workflows start writing catalog records"
    source: "Milestone 2 implementation"
    revisit_when: "Before adding transactional MCP tools"
  - signal: "Graph traversal is needed for supplier substitutions"
    source: "Milestone 1 follow-up"
    revisit_when: "Before enabling AGE"
---

# ADR-0002: Relational catalog as the source of truth

## Context

Milestone 1 needs current pizza recipes and declared allergens. Twelve existing
PDFs contain fictional editorial examples, not certified supplier declarations.
The planned supplier and substitution graph must not duplicate authoritative
allergen facts.

## Options

- One relational HorizonDB catalog with read-only MCP tools, reserving AGE for
  a later derived graph: small, verifiable first increment.
- AGE as the primary catalog: expressive paths, but graph maintenance and
  validation complicate simple recipe and allergen lookups.
- Separate relational and graph clusters now: independent scaling, but
  unnecessary operational cost and consistency work for the demo.

## Decision and rationale

Use PostgreSQL 17 tables for pizzas, recipe items, ingredients, known ingredient
allergens and the 14 numbered allergen names. Versioned fictional JSON fixtures
seed the catalog reproducibly. The runtime MCP identity reads only; seeding
uses a separate elevated identity. All tool results identify demo data and
retain uncertainty for ingredients with unverified supplier composition.
Expose only bounded read-only searches and lookups through authenticated
Streamable HTTP; keep the document PDFs editorial.

## Consequences

An ingredient not declaring an allergen is never proof of food safety or of
freedom from cross-contact. PRICE and availability are also simulated. If AGE
is introduced, model suppliers and substitutions as a separate derived graph
in the existing HorizonDB cluster and validate it against catalog IDs; the
relational recipe remains authoritative. HorizonDB/AGE are preview services;
review availability and costs before provisioning.

Microsoft's [HorizonDB overview](https://learn.microsoft.com/azure/horizondb/overview)
lists Sweden Central and preview limitations; the
[AGE guide](https://learn.microsoft.com/azure/horizondb/graph/age-overview)
documents the graph extension and its required cluster parameters.
