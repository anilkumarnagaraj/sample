variable "access_group_name" {
  type        = string
}

variable "roles" {
  type        = list(string)
  default     = []
}