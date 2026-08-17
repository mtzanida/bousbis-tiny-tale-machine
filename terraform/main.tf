provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "Bousbis Tiny Tale Machine"
      ManagedBy = "Terraform"
      Challenge = "AWS Weekend Creative Challenge"
    }
  }
}
