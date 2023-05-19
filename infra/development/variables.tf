variable "env" {
  description = "Environment name"
  default     = "development"
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

variable "security_group_ids" {
  description = "Security group ID"
  default     = ["sg-0a97fbfa3e8ac6431"]
}

variable "vpc_ids" {
  description = "VPC ID"
  default     = ["vpc-0476e4a5a983d1193"]
}
