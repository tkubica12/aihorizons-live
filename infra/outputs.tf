output "resource_group_id" {
  description = "Azure resource ID of the project resource group."
  value       = azapi_resource.resource_group.id
}

output "storage_account_id" {
  description = "Azure resource ID of the document storage account."
  value       = azapi_resource.document_storage.id
}

output "storage_account_name" {
  description = "Name of the document storage account."
  value       = azapi_resource.document_storage.name
}

output "pizza_pdfs_container_name" {
  description = "Private blob container for the demo pizza PDF files."
  value       = azapi_resource.pizza_pdfs.name
}

output "foundry_project_id" {
  description = "Azure resource ID of the imported Foundry project."
  value       = azapi_resource.foundry_project.id
}

output "foundry_model_id" {
  description = "Azure resource ID of the imported model deployment."
  value       = azapi_resource.foundry_model.id
}

output "container_registry_login_server" {
  description = "Registry login server for the Python MCP image."
  value       = "${azapi_resource.container_registry.name}.azurecr.io"
}

output "secrets_vault_uri" {
  description = "Key Vault URI for database and MCP credentials."
  value       = "https://${azapi_resource.secrets_vault.name}.vault.azure.net/"
}

output "container_environment_id" {
  description = "Azure Container Apps environment ID."
  value       = azapi_resource.container_environment.id
}
