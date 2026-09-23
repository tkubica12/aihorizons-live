variable "horizondb_admin_password" {
  description = "HorizonDB admin password supplied from Key Vault for each Terraform run."
  type        = string
  sensitive   = true
  ephemeral   = true
}

resource "azapi_resource" "horizondb" {
  type      = "Microsoft.HorizonDB/clusters@2026-01-20-preview"
  name      = "hdb-aihorizons"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    properties = {
      createMode          = "Create"
      version             = "17"
      administratorLogin  = "aihadmin"
      vCores              = 2
      replicaCount        = 1
      zonePlacementPolicy = "BestEffort"
    }
  }

  sensitive_body = {
    properties = {
      administratorLoginPassword = var.horizondb_admin_password
    }
  }

  sensitive_body_version = {
    "properties.administratorLoginPassword" = "1"
  }

  lifecycle {
    prevent_destroy = true
  }
}

output "horizondb_cluster_id" {
  description = "HorizonDB PostgreSQL cluster resource ID."
  value       = azapi_resource.horizondb.id
}
