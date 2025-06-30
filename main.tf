#resource "ibm_is_vpc" "vpc" {
#  name = var.vpc_name
#}


#data "ibm_code_engine_app" "code_engine_app" {
#  name       = var.app_name
#  project_id = var.project_id
#}

#output "app_details" {
#  value = data.ibm_code_engine_app.code_engine_app
#}

data "ibm_resource_group" "resource_group" {
   name = var.your_resource_group_name
}

resource "ibm_code_engine_project" "code_engine_project_instance" {
   name = var.project_name
   resource_group_id = data.ibm_resource_group.resource_group.id
}
