variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "monitoring-rg"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "westeurope"
}

variable "prefix" {
  description = "Prefix for all resources"
  type        = string
  default     = "monitoring"
}

variable "acr_name" {
  description = "Azure Container Registry name"
  type        = string
  default     = "shiyomonitoring001"
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = "nayakvinay28@gmail.com"
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
  default = {
    Environment = "dev"
    Project     = "monitoring"
    ManagedBy   = "terraform"
  }
}
