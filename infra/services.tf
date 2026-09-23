resource "azapi_resource" "container_registry" {
  type      = "Microsoft.ContainerRegistry/registries@2025-04-01"
  name      = "aihorizons673af34dacr"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    sku = {
      name = "Basic"
    }
    properties = {
      adminUserEnabled     = false
      anonymousPullEnabled = false
      publicNetworkAccess  = "Enabled"
    }
  }
}

resource "azapi_resource" "secrets_vault" {
  type      = "Microsoft.KeyVault/vaults@2024-11-01"
  name      = "kvaihorizons673af34d"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    properties = {
      tenantId                  = "6ce4f237-667f-43f5-aafd-cbef954adf97"
      sku                       = { family = "A", name = "standard" }
      enableRbacAuthorization   = true
      softDeleteRetentionInDays = 7
      publicNetworkAccess       = "Enabled"
    }
  }
}

resource "azapi_resource" "container_environment" {
  type      = "Microsoft.App/managedEnvironments@2025-01-01"
  name      = "cae-aihorizons"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    properties = {
      workloadProfiles = [
        {
          name                = "Consumption"
          workloadProfileType = "Consumption"
        }
      ]
    }
  }
}
