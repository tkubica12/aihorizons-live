variable "staff_mcp_image" {
  description = "Digest-pinned pizza-mcp image containing staff_server.py; empty skips new deployment."
  type        = string
  default     = ""
}

variable "external_agent_image" {
  description = "Digest-pinned LangGraph hello image; empty skips new deployment."
  type        = string
  default     = ""
}

resource "azapi_resource" "foundry_registry_pull" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = uuidv5("url", "${azapi_resource.container_registry.id}/foundry-project/acr-pull")
  parent_id = azapi_resource.container_registry.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/7f951dda-4ed3-4680-a7ca-43fe172d538d"
      principalId      = azapi_resource.foundry_project.output.identity.principalId
      principalType    = "ServicePrincipal"
    }
  }
}

resource "azapi_resource" "staff_order_app" {
  count     = var.staff_mcp_image == "" ? 0 : 1
  type      = "Microsoft.App/containerApps@2025-01-01"
  name      = "pizza-staff-order-mcp"
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
        registries = [{
          server   = "${azapi_resource.container_registry.name}.azurecr.io"
          identity = azapi_resource.mcp_identity.id
        }]
        secrets = [
          {
            name        = "database-url"
            keyVaultUrl = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/secrets/orderdb-runtime-url"
            identity    = azapi_resource.mcp_identity.id
          },
          {
            name        = "staff-token"
            keyVaultUrl = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/secrets/mcp-staff-api-token"
            identity    = azapi_resource.mcp_identity.id
          }
        ]
      }
      template = {
        containers = [{
          name    = "staff-orders"
          image   = var.staff_mcp_image
          command = ["uvicorn", "pizza_mcp.staff_server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
          resources = {
            cpu    = 0.5
            memory = "1Gi"
          }
          env = [
            { name = "DATABASE_URL", secretRef = "database-url" },
            { name = "MCP_API_TOKEN", secretRef = "staff-token" },
            {
              name  = "MCP_ALLOWED_HOST"
              value = "pizza-staff-order-mcp.${azapi_resource.container_environment_vnet.output.properties.defaultDomain}"
            }
          ]
          probes = [{
            type = "Readiness"
            httpGet = {
              path = "/healthz"
              port = 8000
            }
            periodSeconds       = 10
            timeoutSeconds      = 5
            failureThreshold    = 6
            initialDelaySeconds = 10
          }]
        }]
        scale = {
          minReplicas = 0
          maxReplicas = 1
        }
      }
    }
  }

  depends_on = [azapi_resource.order_app]
}

resource "azapi_resource" "external_hello_app" {
  count     = var.external_agent_image == "" ? 0 : 1
  type      = "Microsoft.App/containerApps@2025-01-01"
  name      = "pizza-hello-external"
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
        registries = [{
          server   = "${azapi_resource.container_registry.name}.azurecr.io"
          identity = azapi_resource.mcp_identity.id
        }]
        secrets = [{
          name        = "hello-token"
          keyVaultUrl = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/secrets/external-hello-api-token"
          identity    = azapi_resource.mcp_identity.id
        }]
      }
      template = {
        containers = [{
          name  = "hello"
          image = var.external_agent_image
          resources = {
            cpu    = 0.5
            memory = "1Gi"
          }
          env = [
            { name = "HELLO_API_TOKEN", secretRef = "hello-token" },
            {
              name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
              value = azapi_resource.foundry_app_insights.output.properties.ConnectionString
            }
          ]
          probes = [{
            type = "Readiness"
            httpGet = {
              path = "/healthz"
              port = 8000
            }
            periodSeconds       = 10
            timeoutSeconds      = 5
            failureThreshold    = 6
            initialDelaySeconds = 10
          }]
        }]
        scale = {
          minReplicas = 0
          maxReplicas = 1
        }
      }
    }
  }
}

output "staff_orders_mcp_url" {
  value = var.staff_mcp_image == "" ? null : "https://${azapi_resource.staff_order_app[0].output.properties.configuration.ingress.fqdn}/mcp"
}

output "external_hello_url" {
  value = var.external_agent_image == "" ? null : "https://${azapi_resource.external_hello_app[0].output.properties.configuration.ingress.fqdn}/chat"
}
