resource "azapi_resource" "mcp_identity" {
  type      = "Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31"
  name      = "id-pizza-mcp"
  parent_id = azapi_resource.resource_group.id
  location  = var.location
}

resource "azapi_resource" "mcp_registry_pull" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = uuidv5("url", "${azapi_resource.container_registry.id}/id-pizza-mcp/acr-pull")
  parent_id = azapi_resource.container_registry.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/7f951dda-4ed3-4680-a7ca-43fe172d538d"
      principalId      = azapi_resource.mcp_identity.output.properties.principalId
      principalType    = "ServicePrincipal"
    }
  }
}

resource "azapi_resource" "mcp_vault_secrets_user" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = uuidv5("url", "${azapi_resource.secrets_vault.id}/id-pizza-mcp/secrets-user")
  parent_id = azapi_resource.secrets_vault.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/4633458b-17de-408a-b874-0445c86b69e6"
      principalId      = azapi_resource.mcp_identity.output.properties.principalId
      principalType    = "ServicePrincipal"
    }
  }
}
