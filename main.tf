module "access-group" {
  source = "./modules/access-group"

  access_group_name = var.access_group_name
  roles             = var.roles
}