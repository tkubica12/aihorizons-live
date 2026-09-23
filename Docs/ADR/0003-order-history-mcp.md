# ADR 0003: Separate read-only order-history MCP

## Context

The product catalog answers questions about pizzas, not a customer's previous
transactions. Milestone 2 of the PRD introduces fictional customer profiles
and orders. A second example should demonstrate a different data shape
without pretending that order placement or identity verification already works.

## Decision

Store demo customers, orders and line items in three relational tables in the
same HorizonDB cluster as the catalog. Run an independent Python MCP process
from the same versioned image with `pizza_mcp.order_server:app` as its entry
point. Keep historical pizza names and prices on order items; the foreign key
to `pizza` retains referential integrity. All read tools require an explicit
fictional `customer_id` and scope order lookups by it. Favorite and spend
aggregates count only delivered orders. The endpoint uses the same bearer
protection as the catalog, but profile selection is **not authentication**.

## Alternatives and consequences

A separate database would add administration with no isolation advantage for
this small demonstration; a merged MCP would obscure the two domain examples.
Shipment belongs to milestone 3. Pizza customization is another catalog
operation rather than a distinct historical dataset. This read-only endpoint
does not create orders, charge payments, or authorize real customers. Before
real customer use, add verified identity and authorization, a transactional
write flow, and appropriate privacy controls. Seed existing order IDs with
`ON CONFLICT DO NOTHING` so re-running fixtures does not overwrite later
status changes; seed must run after catalog seed.

## Review conditions

Verify that all five tools return structured records, detail lookup cannot
return an order from a different selected profile, totals use stored unit
prices and only delivered orders enter favorites/spend. Verify the deployed
MCP against actual seeded rows rather than a mocked response.
