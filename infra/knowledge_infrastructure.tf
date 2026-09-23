resource "azapi_resource" "knowledge_search" {
  type      = "Microsoft.Search/searchServices@2025-05-01"
  name      = "aihorizons-srch-swdh"
  parent_id = azapi_resource.resource_group.id
  location  = "westeurope"

  identity {
    type         = "SystemAssigned"
    identity_ids = []
  }

  body = {
    sku = {
      name = "standard"
    }
    properties = {
      disableLocalAuth    = true
      hostingMode         = "Default"
      partitionCount      = 1
      replicaCount        = 1
      semanticSearch      = "standard"
      publicNetworkAccess = "Enabled"
      networkRuleSet = {
        bypass  = "None"
        ipRules = []
      }
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "knowledge_search_blob_reader" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = "a1dc9320-ae5b-43aa-9e62-fc12f04a56d8"
  parent_id = azapi_resource.document_storage.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/2a2b9908-6ea1-4ae2-8e65-a410df84e7d1"
      principalId      = azapi_resource.knowledge_search.output.identity.principalId
      principalType    = "ServicePrincipal"
    }
  }
}

resource "azapi_resource" "foundry_search_index_reader" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = "e5931faa-a4ec-477d-a9bd-b8e9c67c8ef7"
  parent_id = azapi_resource.knowledge_search.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/1407120a-92aa-4202-b7e9-c0e197c71c8f"
      principalId      = azapi_resource.foundry_project.output.identity.principalId
      principalType    = "ServicePrincipal"
    }
  }
}

resource "azapi_resource" "foundry_logs" {
  type      = "Microsoft.OperationalInsights/workspaces@2023-09-01"
  name      = "aihorizons-resource-logs"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    properties = {
      sku = {
        name = "PerGB2018"
      }
      retentionInDays                 = 30
      publicNetworkAccessForIngestion = "Enabled"
      publicNetworkAccessForQuery     = "Enabled"
      features = {
        enableLogAccessUsingOnlyResourcePermissions = true
      }
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_app_insights" {
  type      = "Microsoft.Insights/components@2020-02-02"
  name      = "aihorizons-resource-appinsights"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    kind = "web"
    properties = {
      Application_Type                = "web"
      Flow_Type                       = "Bluefield"
      Request_Source                  = "rest"
      IngestionMode                   = "LogAnalytics"
      RetentionInDays                 = 90
      publicNetworkAccessForIngestion = "Enabled"
      publicNetworkAccessForQuery     = "Enabled"
      WorkspaceResourceId             = azapi_resource.foundry_logs.id
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "container_subnet_nsg" {
  type      = "Microsoft.Network/networkSecurityGroups@2024-05-01"
  name      = "vnet-aihorizons-snet-container-apps-nsg-swedencentral"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    properties = {
      securityRules = []
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "database_endpoint_subnet_nsg" {
  type      = "Microsoft.Network/networkSecurityGroups@2024-05-01"
  name      = "vnet-aihorizons-snet-private-endpoints-nsg-swedencentral"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    properties = {
      securityRules = []
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_guardrails" {
  type      = "Microsoft.CognitiveServices/accounts/raiPolicies@2025-06-01"
  name      = "Guardrails402"
  parent_id = azapi_resource.foundry_account.id

  body = {
    properties = jsondecode(file("${path.module}/guardrails-402.json"))
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_search_connection" {
  type      = "Microsoft.CognitiveServices/accounts/connections@2025-06-01"
  name      = "aihorizonssrchswdh0mtcxs"
  parent_id = azapi_resource.foundry_account.id

  body = {
    properties = {
      authType                    = "AAD"
      category                    = "CognitiveSearch"
      isSharedToAll               = false
      useWorkspaceManagedIdentity = false
      target                      = "https://aihorizons-srch-swdh.search.windows.net/"
      metadata = {
        ApiType              = "Azure"
        ApiVersion           = "2024-05-01-preview"
        DeploymentApiVersion = "2023-11-01"
        ResourceId           = azapi_resource.knowledge_search.id
        displayName          = azapi_resource.knowledge_search.name
        type                 = "azure_ai_search"
      }
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_failure_alert" {
  type      = "Microsoft.AlertsManagement/smartDetectorAlertRules@2021-04-01"
  name      = "Failure Anomalies - aihorizons-resource-appinsights"
  parent_id = azapi_resource.resource_group.id
  location  = "global"

  body = {
    properties = {
      description = "Failure Anomalies notifies you of an unusual rise in the rate of failed HTTP requests or dependency calls."
      frequency   = "PT1M"
      severity    = "Sev3"
      state       = "Enabled"
      scope       = [lower(azapi_resource.foundry_app_insights.id)]
      detector = {
        id = "FailureAnomaliesDetector"
      }
      actionGroups = {
        groupIds = [
          "/subscriptions/${var.subscription_id}/resourcegroups/ai-services/providers/microsoft.insights/actiongroups/application insights smart detection"
        ]
      }
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}
