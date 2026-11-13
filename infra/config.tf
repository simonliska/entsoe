# config/datasets.yaml is the source of truth: one SSM parameter per dataset, read by the Lambda.
locals {
  datasets      = yamldecode(file("${path.module}/../config/datasets.yaml"))
  config_prefix = "/${local.name}/datasets"
}

resource "aws_ssm_parameter" "dataset" {
  for_each = local.datasets

  name  = "${local.config_prefix}/${each.key}"
  type  = "String"
  value = jsonencode(each.value)
}
