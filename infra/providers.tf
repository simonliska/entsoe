provider "aws" {
  region = var.region

  default_tags {
    tags = { Project = "entsoe-scraper", ManagedBy = "terraform" }
  }
}
