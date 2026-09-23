resource "azapi_resource" "static_egress_ip" {
  count     = var.database_network_mode == "static_egress" ? 1 : 0
  type      = "Microsoft.Network/publicIPAddresses@2024-05-01"
  name      = "pip-aihorizons-nat"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    sku = {
      name = "Standard"
      tier = "Regional"
    }
    properties = {
      publicIPAllocationMethod = "Static"
    }
  }
}

resource "azapi_resource" "static_egress_nat" {
  count     = var.database_network_mode == "static_egress" ? 1 : 0
  type      = "Microsoft.Network/natGateways@2024-05-01"
  name      = "nat-aihorizons-mcp"
  parent_id = azapi_resource.resource_group.id
  location  = var.location

  body = {
    sku = {
      name = "Standard"
    }
    properties = {
      idleTimeoutInMinutes = 10
      publicIpAddresses = [
        {
          id = azapi_resource.static_egress_ip[0].id
        }
      ]
    }
  }
}

resource "azapi_resource" "horizondb_static_egress_rule" {
  count     = var.database_network_mode == "static_egress" ? 1 : 0
  type      = "Microsoft.HorizonDB/clusters/pools/firewallRules@2026-01-20-preview"
  name      = "allow-aihorizons-mcp"
  parent_id = "${azapi_resource.horizondb.id}/pools/DefaultPool"

  body = {
    properties = {
      startIpAddress = azapi_resource.static_egress_ip[0].output.properties.ipAddress
      endIpAddress   = azapi_resource.static_egress_ip[0].output.properties.ipAddress
      description    = "Only the AI Horizons Container Apps NAT egress IP"
    }
  }

  depends_on = [azapi_resource.container_subnet]
}

resource "azapi_resource" "horizondb_azure_services_rule" {
  count     = var.database_network_mode == "azure_services" ? 1 : 0
  type      = "Microsoft.HorizonDB/clusters/pools/firewallRules@2026-01-20-preview"
  name      = "allow-azure-services-demo"
  parent_id = "${azapi_resource.horizondb.id}/pools/DefaultPool"

  body = {
    properties = {
      startIpAddress = "0.0.0.0"
      endIpAddress   = "0.0.0.0"
    }
  }
}
