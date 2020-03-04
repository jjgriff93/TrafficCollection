# Create a new resource group
resource "azurerm_resource_group" "trafficdata" {
  name     = "rg-${var.appname}-${var.environment}-traffic"
  location = var.location
}

# Key Vault for the Azure Maps key
resource "azurerm_key_vault" "traffic_collection" {
  name                = "kv-${var.appname}-traffic-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.trafficdata.name
  tenant_id           = var.tenant_id

  sku_name = "standard"

  network_acls {
    default_action = "Allow"
    bypass         = "None"
  }
}

resource "azurerm_key_vault_access_policy" "client_keyvault" {
  key_vault_id = azurerm_key_vault.traffic_collection.id

  tenant_id = var.tenant_id
  object_id = var.client_id

  secret_permissions = [
    "get",
    "set",
    "delete",
  ]
}

resource "azurerm_key_vault_access_policy" "function_keyvault" {
  key_vault_id = azurerm_key_vault.traffic_collection.id

  tenant_id = azurerm_function_app.trafficdata.identity[0].tenant_id
  object_id = azurerm_function_app.trafficdata.identity[0].principal_id

  secret_permissions = [
    "get",
  ]
}

resource "azurerm_key_vault_secret" "traffic_collection" {
  name         = "mapskey"
  value        = var.maps_key
  key_vault_id = azurerm_key_vault.traffic_collection.id
  depends_on = [azurerm_key_vault_access_policy.client_keyvault]
}


# Storage for the Azure Functions output
resource "azurerm_storage_account" "trafficdata" {
  name                     = "st${var.appname}traffic${var.environment}"
  resource_group_name      = azurerm_resource_group.trafficdata.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "RAGRS"
  account_kind             = "StorageV2"
}

# Two outpout blob containers
resource "azurerm_storage_container" "trafficroutes" {
  name                  = "trafficroutes"
  storage_account_name  = azurerm_storage_account.trafficdata.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "traffictiles" {
  name                  = "traffictiles"
  storage_account_name  = azurerm_storage_account.trafficdata.name
  container_access_type = "private"
}

# Function access to blob storage containers access

resource "azurerm_role_assignment" "trafficdata" {
  scope                = azurerm_storage_account.trafficdata.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_function_app.trafficdata.identity[0].principal_id
}

resource "azurerm_role_assignment" "config" {
  scope                = var.config_storage_id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_function_app.trafficdata.identity[0].principal_id
}

# Storage for the Azure Functions metadata
resource "azurerm_storage_account" "trafficdatafunctions" {
  name                     = "st${var.appname}traffun${var.environment}"
  resource_group_name      =  azurerm_resource_group.trafficdata.name
  location                 =  var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_app_service_plan" "trafficdata" {
  name                = "plan-${var.appname}-traffic-${var.environment}"
  resource_group_name =  azurerm_resource_group.trafficdata.name
  location            =  var.location
  kind                =  "linux"
  reserved            =  true

  sku {
    tier = "Basic"
    size = "B1"
  }
}

resource "azurerm_function_app" "trafficdata" {
  name                      = "func-${var.appname}-traffic-${var.environment}"
  resource_group_name       = azurerm_resource_group.trafficdata.name
  location                  = var.location
  app_service_plan_id       = azurerm_app_service_plan.trafficdata.id
  storage_connection_string = azurerm_storage_account.trafficdatafunctions.primary_connection_string
  version                   = "~2"
  app_settings              = {
      "CITIES_CONFIG_URL"               = var.config_cities_url
      "TRAFFICTILES_OUTPUT_URL"         = azurerm_storage_container.traffictiles.id
      "TRAFFICROUTES_OUTPUT_URL"        = azurerm_storage_container.trafficroutes.id
      "AZURE_MAPS_ENDPOINT"             = "https://atlas.microsoft.com/"
      "KEY_VAULT"                       = azurerm_key_vault.traffic_collection.vault_uri
      "NUM_OF_ROUTES_PER_CITY"          = var.nb_of_routes
      "FUNCTIONS_WORKER_RUNTIME"        = "python"
      "WEBSITE_NODE_DEFAULT_VERSION"    = "~10"
      "APPINSIGHTS_INSTRUMENTATIONKEY"  = var.appinsights_instrumentation_key
  }

  identity {
    type = "SystemAssigned"
  }

  site_config {
    linux_fx_version = "PYTHON|3.7"
  }

}
