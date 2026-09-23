locals {
  foundry_operator_principal_id = "e011e2a1-33d6-418f-b2ed-35f7d2281f45"
}

resource "azapi_resource" "foundry_operator_rg_user" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = "0ff82b89-b1d8-4d78-a8ac-64cb4c895dd8"
  parent_id = azapi_resource.resource_group.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/53ca6127-db72-4b80-b1b0-d745d6d5456d"
      principalId      = local.foundry_operator_principal_id
      principalType    = "User"
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_operator_search_service_contributor" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = "d271b554-e17c-470e-9fd3-d38b1b354993"
  parent_id = azapi_resource.knowledge_search.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/7ca78c08-252a-4471-8644-bb5ff32d4ba0"
      principalId      = local.foundry_operator_principal_id
      principalType    = "User"
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_operator_search_index_contributor" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = "936dab53-1a23-4302-abaa-d95839533f11"
  parent_id = azapi_resource.knowledge_search.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/8ebe5a00-799e-43f5-93ac-243d3dce84a7"
      principalId      = local.foundry_operator_principal_id
      principalType    = "User"
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azapi_resource" "foundry_project_self_user" {
  type      = "Microsoft.Authorization/roleAssignments@2022-04-01"
  name      = "a6a36912-9455-4cdc-b1c9-8ea4a1dbcd78"
  parent_id = azapi_resource.foundry_project.id

  body = {
    properties = {
      roleDefinitionId = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/53ca6127-db72-4b80-b1b0-d745d6d5456d"
      principalId      = azapi_resource.foundry_project.output.identity.principalId
      principalType    = "ServicePrincipal"
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}
