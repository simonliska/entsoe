output "data_bucket" {
  value = aws_s3_bucket.data.bucket
}

output "token_parameter" {
  value = aws_ssm_parameter.token.name
}

output "function_name" {
  value = aws_lambda_function.scraper.function_name
}
