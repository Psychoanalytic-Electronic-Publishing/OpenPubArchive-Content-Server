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

variable "vpc_ids" {
  description = "VPC ID"
  default     = ["vpc-0476e4a5a983d1193"]
}

variable "security_group_ids" {
  description = "Security group ID"
  default     = ["sg-0a97fbfa3e8ac6431"]
}
