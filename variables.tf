variable "access_group_name" {
  description = "Access group name"
  type        = string
  default     = "sample-grp-01"
}

variable "roles" {
  type    = list(string)
  default = ["Writer"]
}