terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.0"
    }
  }
}

variable "subscription_id" {
  description = "Azure subscription that owns the project resources."
  type        = string
  default     = "673af34d-6b28-41dc-bc7b-f507418045e6"
}

variable "location" {
  description = "Azure region for the initial project resources."
  type        = string
  default     = "swedencentral"
}

variable "storage_account_name" {
  description = "Globally unique, lowercase name of the document storage account."
  type        = string
  default     = "aihorizons673af34ddocs"

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "The storage account name must be 3-24 lowercase letters or digits."
  }
}

provider "azapi" {
  subscription_id = var.subscription_id
}

resource "azapi_resource" "resource_group" {
  type     = "Microsoft.Resources/resourceGroups@2023-07-01"
  name     = "RG-AI-Horizons"
  location = var.location

  tags = {
    "Security Controls" = "ignore"
    SecurityControl     = "Ignore"
  }
}

resource "azapi_resource" "document_storage" {
  type      = "Microsoft.Storage/storageAccounts@2023-05-01"
  name      = var.storage_account_name
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    kind = "StorageV2"
    sku = {
      name = "Standard_LRS"
    }
    properties = {
      accessTier                   = "Hot"
      allowBlobPublicAccess        = false
      allowSharedKeyAccess         = false
      defaultToOAuthAuthentication = true
      minimumTlsVersion            = "TLS1_2"
      supportsHttpsTrafficOnly     = true
      publicNetworkAccess          = "Enabled"
      networkAcls = {
        defaultAction = "Allow"
      }
    }
  }
}

resource "azapi_resource" "pizza_pdfs" {
  type      = "Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01"
  name      = "pizza-pdfs"
  parent_id = "${azapi_resource.document_storage.id}/blobServices/default"

  body = {
    properties = {
      publicAccess = "None"
    }
  }
}
