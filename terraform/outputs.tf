output "functions_name" {
  value = azurerm_function_app.trafficdata.name
}

output "traffic_collection_rg" {
  value = azurerm_resource_group.trafficdata.name
}