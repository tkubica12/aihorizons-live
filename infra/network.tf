variable "database_network_mode" {
  description = "Temporary Azure-wide demo rule; switch to private_endpoint after subscription feature registration."
  type        = string
  default     = "azure_services"

  validation {
    condition     = contains(["private_endpoint", "static_egress", "azure_services"], var.database_network_mode)
    error_message = "Use private_endpoint, static_egress or azure_services."
  }
}

resource "azapi_resource" "service_vnet" {
  type      = "Microsoft.Network/virtualNetworks@2024-05-01"
  name      = "vnet-aihorizons"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    properties = {
      addressSpace = {
        addressPrefixes = ["10.42.0.0/24"]
      }
    }
  }
}

resource "azapi_resource" "container_subnet" {
  type      = "Microsoft.Network/virtualNetworks/subnets@2024-05-01"
  name      = "snet-container-apps"
  parent_id = azapi_resource.service_vnet.id

  body = {
    properties = merge({
      addressPrefix = "10.42.0.0/27"
      delegations = [
        {
          name = "container-apps"
          properties = {
            serviceName = "Microsoft.App/environments"
          }
        }
      ]
      }, var.database_network_mode == "static_egress" ? {
      natGateway = {
        id = azapi_resource.static_egress_nat[0].id
      }
    } : {})
  }
}

resource "azapi_resource" "database_endpoint_subnet" {
  type      = "Microsoft.Network/virtualNetworks/subnets@2024-05-01"
  name      = "snet-private-endpoints"
  parent_id = azapi_resource.service_vnet.id

  body = {
    properties = {
      addressPrefix = "10.42.0.32/27"
    }
  }

  depends_on = [azapi_resource.container_subnet]
}

resource "azapi_resource" "horizondb_dns" {
  type      = "Microsoft.Network/privateDnsZones@2024-06-01"
  name      = "privatelink.horizondb.azure.com"
  parent_id = azapi_resource.resource_group.id
  location  = "global"
}

resource "azapi_resource" "horizondb_dns_link" {
  type      = "Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01"
  name      = "aihorizons-vnet"
  parent_id = azapi_resource.horizondb_dns.id
  location  = "global"

  body = {
    properties = {
      registrationEnabled = false
      virtualNetwork = {
        id = azapi_resource.service_vnet.id
      }
    }
  }
}

resource "azapi_resource" "horizondb_private_endpoint" {
  count     = var.database_network_mode == "private_endpoint" ? 1 : 0
  type      = "Microsoft.Network/privateEndpoints@2024-05-01"
  name      = "pe-hdb-aihorizons"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    properties = {
      subnet = {
        id = azapi_resource.database_endpoint_subnet.id
      }
      privateLinkServiceConnections = [
        {
          name = "horizondb"
          properties = {
            privateLinkServiceId = azapi_resource.horizondb.id
            groupIds             = ["DefaultPool"]
          }
        }
      ]
    }
  }
}

resource "azapi_resource" "horizondb_dns_zone_group" {
  count     = var.database_network_mode == "private_endpoint" ? 1 : 0
  type      = "Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01"
  name      = "horizondb"
  parent_id = azapi_resource.horizondb_private_endpoint[0].id

  body = {
    properties = {
      privateDnsZoneConfigs = [
        {
          name = "horizondb"
          properties = {
            privateDnsZoneId = azapi_resource.horizondb_dns.id
          }
        }
      ]
    }
  }
}

resource "azapi_resource" "container_environment_vnet" {
  type      = "Microsoft.App/managedEnvironments@2025-01-01"
  name      = "cae-aihorizons-vnet"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    properties = {
      vnetConfiguration = {
        infrastructureSubnetId = azapi_resource.container_subnet.id
        internal               = false
      }
      workloadProfiles = [
        {
          name                = "Consumption"
          workloadProfileType = "Consumption"
        }
      ]
    }
  }
}
