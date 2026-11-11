resource "aws_ssm_parameter" "token" {
  name             = "/${local.name}/entsoe-token"
  type             = "SecureString"
  value_wo         = var.entsoe_token
  value_wo_version = var.entsoe_token_version
}
