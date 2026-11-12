variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "entsoe_token" {
  description = "ENTSO-E API token"
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "entsoe_token_version" {
  description = "Bump to push a new token value to SSM."
  type        = number
  default     = 1
}
