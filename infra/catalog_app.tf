resource "azapi_resource" "catalog_app" {
  type      = "Microsoft.App/containerApps@2025-01-01"
  name      = "pizza-mcp"
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
            keyVaultUrl = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/secrets/horizondb-runtime-url"
            identity    = azapi_resource.mcp_identity.id
          },
          {
            name        = "mcp-token"
            keyVaultUrl = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/secrets/mcp-api-token"
            identity    = azapi_resource.mcp_identity.id
          }
        ]
      }
      template = {
        containers = [
          {
            name    = "catalog"
            image   = "${azapi_resource.container_registry.name}.azurecr.io/pizza-mcp@sha256:7bc829bf915eb3c32fcb4f27b43c6d15876cd0c079f2a033efb33e913037d9db"
            command = ["uvicorn", "pizza_mcp.server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
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
                value = "pizza-mcp.${azapi_resource.container_environment_vnet.output.properties.defaultDomain}"
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

  depends_on = [
    azapi_resource.mcp_registry_pull,
    azapi_resource.mcp_vault_secrets_user,
    azapi_resource.horizondb_dns_zone_group,
    azapi_resource.horizondb_dns_link,
    azapi_resource.horizondb_static_egress_rule,
    azapi_resource.horizondb_azure_services_rule,
  ]
}

output "catalog_mcp_url" {
  description = "Public HTTPS endpoint for the authenticated catalog MCP."
  value       = "https://${azapi_resource.catalog_app.output.properties.configuration.ingress.fqdn}/mcp"
}
