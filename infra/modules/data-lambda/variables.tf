variable "env" {
  description = "Environment name"
}

variable "aws_region" {
  description = "AWS region"
}

variable "account_id" {
  description = "AWS account ID"
}

variable "stack_name" {
  description = "Root name for the stack"
}

variable "vpc_ids" {
  description = "VPC ID"
}

variable "security_group_ids" {
  description = "Security group ID"
}

variable "repository_url" {
  description = "ECR repository URL"
}
