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

variable "your_resource_group_name" {
  description = "The resource group ID where the Code Engine app resides"
  type        = string
  default     = "Default"  
}

variable "project_name" {
  description = "Code Engine application name"
  type        = string
  default     = "ce-proj-01" 
}
