resource "ibm_iam_access_group" "accgrp" {
  name = var.access_group_name
}

resource "ibm_iam_access_group_policy" "policy" {
  access_group_id = ibm_iam_access_group.accgrp.id
  roles           = var.roles
}