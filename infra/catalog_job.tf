locals {
  catalog_bootstrap = <<-PYTHON
    import os
    import psycopg
    from psycopg import sql
    from pizza_mcp.seed import load_fixture, seed

    with psycopg.connect(
        host=os.environ["DATABASE_HOST"],
        dbname="postgres",
        user="aihadmin",
        password=os.environ["ADMIN_PASSWORD"],
        sslmode="require",
    ) as connection:
        seed(connection, load_fixture())
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'pizza_reader'")
            if cursor.fetchone() is None:
                cursor.execute("CREATE ROLE pizza_reader LOGIN")
            cursor.execute(
                sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                    sql.Identifier("pizza_reader"),
                    sql.Literal(os.environ["RUNTIME_PASSWORD"]),
                )
            )
            cursor.execute("GRANT CONNECT ON DATABASE postgres TO pizza_reader")
            cursor.execute("GRANT USAGE ON SCHEMA public TO pizza_reader")
            cursor.execute(
                "GRANT SELECT ON TABLE pizza, ingredient, allergen, "
                "pizza_ingredient, ingredient_allergen TO pizza_reader"
            )
            cursor.execute(
                "ALTER DEFAULT PRIVILEGES FOR ROLE aihadmin IN SCHEMA public "
                "GRANT SELECT ON TABLES TO pizza_reader"
            )
            cursor.execute(
                "SELECT (SELECT count(*) FROM pizza), "
                "(SELECT count(*) FROM ingredient), "
                "(SELECT count(*) FROM allergen), "
                "(SELECT count(*) FROM pizza_ingredient)"
            )
            print("Catalog counts (pizza/ingredient/allergen/recipe):", cursor.fetchone())
  PYTHON
}

resource "azapi_resource" "catalog_bootstrap_job" {
  type      = "Microsoft.App/jobs@2025-01-01"
  name      = "job-pizza-catalog-bootstrap"
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
            keyVaultUrl = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/secrets/horizondb-runtime-password"
            identity    = azapi_resource.mcp_identity.id
          }
        ]
      }
      template = {
        containers = [
          {
            name    = "catalog-bootstrap"
            image   = "${azapi_resource.container_registry.name}.azurecr.io/pizza-mcp@sha256:7bc829bf915eb3c32fcb4f27b43c6d15876cd0c079f2a033efb33e913037d9db"
            command = ["python", "-c"]
            args    = [local.catalog_bootstrap]
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
    azapi_resource.mcp_registry_pull,
    azapi_resource.mcp_vault_secrets_user,
    azapi_resource.horizondb_dns_zone_group,
    azapi_resource.horizondb_dns_link,
    azapi_resource.horizondb_static_egress_rule,
    azapi_resource.horizondb_azure_services_rule,
  ]
}
