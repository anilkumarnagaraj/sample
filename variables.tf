variable "ibmcloud_api_key" {
  description = "IBM Cloud API Key"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "Region where Code Engine project is deployed"
  type        = string
  default     = "us-east"
}

variable "resource_group_id" {
  description = "The resource group ID where the Code Engine app resides"
  type        = string
}

variable "project_id" {
  description = "Code Engine project ID"
  type        = string
  default     = "e5511317-2c53-409a-b1aa-201e6eaaa2bd" 
}

variable "app_name" {
  description = "Code Engine application name"
  type        = string
  default     = "application-e5" 
}
