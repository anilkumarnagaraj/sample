#resource "ibm_is_vpc" "vpc" {
#  name = var.vpc_name
#}


data "ibm_code_engine_app" "code_engine_app" {
    name = "application-01"
    project_id = "42dd1d57-c71c-465c-bb5f-01815c0bc2d2"
}
