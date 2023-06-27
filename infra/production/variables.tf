variable "env" {
  description = "Environment name"
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "account_id" {
  description = "AWS account ID"
}

variable "stack_name" {
  description = "Root name for the stack"
  default     = "opas"
}

variable "cors_origin" {
  description = "CORS origin"
  default     = "https://pep-web.org"
}

variable "pads_root" {
  description = "Root domain for PaDS"
  default     = "https://pads.pep-web.org"
}

variable "mysql_username" {
  description = "Username for the database"
  sensitive   = true
}

variable "mysql_password" {
  description = "Password for the database"
  sensitive   = true
}

variable "engineer_ips" {
  description = "IPs for PEP engineers (comma delimited)"
  sensitive   = true
  type        = string
}
