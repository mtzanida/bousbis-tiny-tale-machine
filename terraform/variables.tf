variable "aws_region" {
  description = "AWS region in which the serverless backend will be deployed."
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Prefix used for AWS resource names."
  type        = string
  default     = "bousbi-tiny-tale-machine"
}

variable "allowed_origin" {
  description = "Frontend origin allowed by CORS. Use the GitHub Pages origin after the first deployment."
  type        = string
  default     = "*"
}
