# One schedule per dataset in config/datasets.yaml; the payload tells the Lambda which dataset to run.
resource "aws_scheduler_schedule" "dataset" {
  for_each = local.datasets

  name                         = "${local.name}-${each.key}"
  schedule_expression          = each.value.schedule
  schedule_expression_timezone = "Europe/Bratislava"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.scraper.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ dataset = each.key })

    retry_policy {
      maximum_retry_attempts = 2
    }
  }
}
