# GitHub Actions deploys through OIDC: short-lived credentials, no AWS keys stored in GitHub.

variable "github_repo" {
  description = "owner/name of the GitHub repository allowed to deploy"
  type        = string
  default     = "simonliska/entsoe"
}

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_policy_document" "github_assume" {
  for_each = {
    plan  = "repo:${var.github_repo}:pull_request"
    apply = "repo:${var.github_repo}:environment:production"
  }

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [each.value]
    }
  }
}

# Pull requests: read-only + state lock.
resource "aws_iam_role" "github_plan" {
  name               = "entsoe-scraper-github-plan"
  assume_role_policy = data.aws_iam_policy_document.github_assume["plan"].json
}

resource "aws_iam_role_policy_attachment" "github_plan_readonly" {
  role       = aws_iam_role.github_plan.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

data "aws_iam_policy_document" "state_lock" {
  statement {
    actions   = ["s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.state.arn}/entsoe-scraper/*.tflock"]
  }
}

resource "aws_iam_role_policy" "github_plan_state_lock" {
  name   = "state-lock"
  role   = aws_iam_role.github_plan.id
  policy = data.aws_iam_policy_document.state_lock.json
}

# main branch via the "production" environment: full deploy rights.
resource "aws_iam_role" "github_apply" {
  name               = "entsoe-scraper-github-apply"
  assume_role_policy = data.aws_iam_policy_document.github_assume["apply"].json
}

resource "aws_iam_role_policy_attachment" "github_apply_admin" {
  role       = aws_iam_role.github_apply.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

output "github_plan_role_arn" {
  value = aws_iam_role.github_plan.arn
}

output "github_apply_role_arn" {
  value = aws_iam_role.github_apply.arn
}
