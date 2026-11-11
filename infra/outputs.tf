output "data_bucket" {
  value = aws_s3_bucket.data.bucket
}

output "token_parameter" {
  value = aws_ssm_parameter.token.name
}
