# Interface contracts

Store one versioned, machine-readable source of truth per interface here; add human context only where the schema cannot express intent. Choose format by interface:

- REST: OpenAPI YAML (`<service>.openapi.yaml`).
- Async messages: AsyncAPI YAML (`<service>.asyncapi.yaml`) with referenced JSON Schemas (`<message>.schema.json`) where useful.
- GraphQL: SDL (`<service>.graphql`).
- MCP: protocol-facing tool/resource definitions with JSON Schema for inputs/outputs (`<server>.mcp.json`), or a generated schema exported from the implementation.
- Other interfaces: established schema format for that protocol; document compatibility and versioning.

Keep implementations and consumer/provider tests aligned with each contract. No contract exists until an interface exists.
