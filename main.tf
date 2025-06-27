#resource "ibm_is_vpc" "vpc" {
#  name = var.vpc_name
#}


data "ibm_code_engine_app" "code_engine_app" {
  name       = var.app_name
  project_id = var.project_id
  resource_group_id = var.resource_group_id 
}

output "app_details" {
  value = data.ibm_code_engine_app.code_engine_app
}
