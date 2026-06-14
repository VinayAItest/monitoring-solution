terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstate2026vinay"
    container_name       = "tfstate"
    key                  = "monitoring.tfstate"
  }
}

provider "azurerm" {
  features {}
  subscription_id = "5e445ad6-3cbb-4c06-b4aa-4429e91115d2"
}

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

resource "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = var.tags
}

resource "azurerm_service_plan" "main" {
  name                = "${var.prefix}-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "F1"
  tags                = var.tags
}

resource "azurerm_linux_web_app" "main" {
  name                = "${var.prefix}-webapp"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id
  tags                = var.tags

  site_config {
    always_on = false
    application_stack {
      docker_image_name        = "monitoring-app:latest"
      docker_registry_url      = "https://${azurerm_container_registry.acr.login_server}"
      docker_registry_username = azurerm_container_registry.acr.admin_username
      docker_registry_password = azurerm_container_registry.acr.admin_password
    }
  }

  app_settings = {
    WEBSITES_PORT = "5000"
  }
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.prefix}-logs"
  resource_group_name = azurerm_resource_group.main.name
  location            =