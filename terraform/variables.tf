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
  description = "Frontend origin allowed by CORS. Set to your GitHub Pages domain, e.g. https://YOUR-USERNAME.github.io"
  type        = string
  default     = "https://mtzanida.github.io"
}

variable "max_concurrency" {
  description = "Maximum number of simultaneous Lambda executions. Limits blast radius from abuse or traffic spikes."
  type        = number
  default     = 10
}
