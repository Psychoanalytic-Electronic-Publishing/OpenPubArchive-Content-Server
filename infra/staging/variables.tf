variable "env" {
  description = "Environment name"
  default     = "staging"
}

variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "account_id" {
  description = "AWS account ID"
  default     = "547758924192"
}

variable "stack_name" {
  description = "Root name for the stack"
  default     = "opas"
}
