#resource "ibm_is_vpc" "vpc" {
#  name = var.vpc_name
#}


data "ibm_code_engine_app" "code_engine_app" {
    name = "application-e5"
    project_id = "e5511317-2c53-409a-b1aa-201e6eaaa2bd"
}
