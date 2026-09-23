locals {
  order_bootstrap = <<-PYTHON
    import os
    import psycopg
    from psycopg import sql
    from pizza_mcp.order_seed import load_orders, seed

    with psycopg.connect(
        host=os.environ["DATABASE_HOST"],
        dbname="postgres",
        user="aihadmin",
        password=os.environ["ADMIN_PASSWORD"],
        sslmode="require",
    ) as connection:
        seed(connection, load_orders())
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'orders_reader'")
            if cursor.fetchone() is None:
                cursor.execute("CREATE ROLE orders_reader LOGIN")
            cursor.execute(
                sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                    sql.Identifier("orders_reader"),
                    sql.Literal(os.environ["RUNTIME_PASSWORD"]),
                )
            )
            cursor.execute("GRANT CONNECT ON DATABASE postgres TO orders_reader")
            cursor.execute("GRANT USAGE ON SCHEMA public TO orders_reader")
            cursor.execute(
                "GRANT SELECT ON TABLE demo_customer, demo_order, demo_order_item "
                "TO orders_reader"
            )
            cursor.execute(
                "SELECT (SELECT count(*) FROM demo_customer), "
                "(SELECT count(*) FROM demo_order), "
                "(SELECT count(*) FROM demo_order_item)"
            )
            print("Order counts (customers/orders/items):", cursor.fetchone())
  PYTHON
}

resource "azapi_resource" "order_bootstrap_job" {
  type      = "Microsoft.App/jobs@2025-01-01"
  name      = "job-pizza-orders-bootstrap"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    identity = {
      type = "UserAssigned"
      userAssignedIdentities = {
        (azapi_resource.mcp_identity.id) = {}
      }
    }
    properties = {
      environmentId = azapi_resource.container_environment_vnet.id
      configuration = {
        triggerType       = "Manual"
        replicaTimeout    = 600
        replicaRetryLimit = 1
        manualTriggerConfig = {
          parallelism            = 1
          replicaCompletionCount = 1
        }
        registries = [
          {
            server   = "${azapi_resource.container_registry.name}.azurecr.io"
            identity = azapi_resource.mcp_identity.id
          }
        ]
        secrets = [
          {
            name        = "admin-password"
            keyVaultUrl = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/secrets/horizondb-admin-password"
            identity    = azapi_resource.mcp_identity.id
          },
          {
            name        = "runtime-password"
            keyVaultUrl = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/secrets/orderdb-runtime-password"
            identity    = azapi_resource.mcp_identity.id
          }
        ]
      }
      template = {
        containers = [
          {
            name    = "orders-bootstrap"
            image   = "${azapi_resource.container_registry.name}.azurecr.io/pizza-mcp@sha256:7bc829bf915eb3c32fcb4f27b43c6d15876cd0c079f2a033efb33e913037d9db"
            command = ["python", "-c"]
            args    = [local.order_bootstrap]
            resources = {
              cpu    = 0.5
              memory = "1Gi"
            }
            env = [
              {
                name  = "DATABASE_HOST"
                value = azapi_resource.horizondb.output.properties.fullyQualifiedDomainName
              },
              {
                name      = "ADMIN_PASSWORD"
                secretRef = "admin-password"
              },
              {
                name      = "RUNTIME_PASSWORD"
                secretRef = "runtime-password"
              }
            ]
          }
        ]
      }
    }
  }

  depends_on = [
    azapi_resource.catalog_bootstrap_job,
    azapi_resource.horizondb_dns_zone_group,
    azapi_resource.horizondb_dns_link,
    azapi_resource.horizondb_static_egress_rule,
    azapi_resource.horizondb_azure_services_rule,
  ]
}

resource "azapi_resource" "order_app" {
  type      = "Microsoft.App/containerApps@2025-01-01"
  name      = "pizza-order-mcp"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    identity = {
      type = "UserAssigned"
      userAssignedIdentities = {
        (azapi_resource.mcp_identity.id) = {}
      }
    }
    properties = {
      environmentId = azapi_resource.container_environment_vnet.id
      configuration = {
        activeRevisionsMode = "Single"
        ingress = {
          external      = true
          targetPort    = 8000
          transport     = "Auto"
          allowInsecure = false
        }
        registries = [
          {
            server   = "${azapi_resource.container_registry.name}.azurecr.io"
            identity = azapi_resource.mcp_identity.id
          }
        ]
        secrets = [
          {
            name        = "database-url"
            keyVaultUrl = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/secrets/orderdb-runtime-url"
            identity    = azapi_resource.mcp_identity.id
          },
          {
            name        = "mcp-token"
            keyVaultUrl = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/secrets/mcp-orders-api-token"
            identity    = azapi_resource.mcp_identity.id
          }
        ]
      }
      template = {
        containers = [
          {
            name    = "orders"
            image   = "${azapi_resource.container_registry.name}.azurecr.io/pizza-mcp@sha256:7bc829bf915eb3c32fcb4f27b43c6d15876cd0c079f2a033efb33e913037d9db"
            command = ["uvicorn", "pizza_mcp.order_server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
            resources = {
              cpu    = 0.5
              memory = "1Gi"
            }
            env = [
              {
                name      = "DATABASE_URL"
                secretRef = "database-url"
              },
              {
                name      = "MCP_API_TOKEN"
                secretRef = "mcp-token"
              },
              {
                name  = "MCP_ALLOWED_HOST"
                value = "pizza-order-mcp.${azapi_resource.container_environment_vnet.output.properties.defaultDomain}"
              }
            ]
            probes = [
              {
                type = "Readiness"
                httpGet = {
                  path = "/healthz"
                  port = 8000
                }
                periodSeconds       = 10
                timeoutSeconds      = 5
                failureThreshold    = 6
                initialDelaySeconds = 10
              }
            ]
          }
        ]
        scale = {
          minReplicas = 0
          maxReplicas = 1
        }
      }
    }
  }

  depends_on = [azapi_resource.order_bootstrap_job]
}

output "orders_mcp_url" {
  description = "Public HTTPS endpoint for the authenticated fictional order MCP."
  value       = "https://${azapi_resource.order_app.output.properties.configuration.ingress.fqdn}/mcp"
}
