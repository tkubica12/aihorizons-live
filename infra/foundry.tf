resource "azapi_resource" "foundry_account" {
  type      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name      = "aihorizons-resource"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  identity {
    type         = "SystemAssigned"
    identity_ids = []
  }

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    properties = {
      allowProjectManagement = true
      apiProperties = {
        qnaAzureSearchEndpointKey = null
      }
      associatedProjects  = ["aihorizons"]
      customSubDomainName = "aihorizons-resource"
      defaultProject      = "aihorizons"
      disableLocalAuth    = false
      publicNetworkAccess = "Enabled"
      networkAcls = {
        defaultAction       = "Allow"
        ipRules             = []
        virtualNetworkRules = []
      }
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_project" {
  type      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name      = "aihorizons"
  parent_id = azapi_resource.foundry_account.id
  location  = var.location

  identity {
    type         = "SystemAssigned"
    identity_ids = []
  }

  body = {
    properties = {}
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_model" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = "gpt-6-sol"
  parent_id = azapi_resource.foundry_account.id

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 477
    }

    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-6-sol"
        version = "2026-09-22"
      }
      raiPolicyName        = "Microsoft.DefaultV2"
      versionUpgradeOption = "OnceNewDefaultVersionAvailable"
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_embedding_model" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = "text-embedding-3-large"
  parent_id = azapi_resource.foundry_account.id

  body = {
    sku = {
      name     = "Standard"
      capacity = 120
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "text-embedding-3-large"
        version = "1"
      }
      raiPolicyName        = "Microsoft.DefaultV2"
      versionUpgradeOption = "OnceNewDefaultVersionAvailable"
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_gpt_54" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = "gpt-5.4"
  parent_id = azapi_resource.foundry_account.id

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 750
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-5.4"
        version = "2026-03-05"
      }
      raiPolicyName        = "Microsoft.DefaultV2"
      versionUpgradeOption = "OnceNewDefaultVersionAvailable"
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_gpt_52" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = "gpt-5.2"
  parent_id = azapi_resource.foundry_account.id

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 250
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-5.2"
        version = "2025-12-11"
      }
      raiPolicyName        = "Microsoft.DefaultV2"
      versionUpgradeOption = "OnceNewDefaultVersionAvailable"
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}
