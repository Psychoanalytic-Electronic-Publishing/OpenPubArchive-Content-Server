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

variable "repository_url" {
  description = "ECR repository URL"
}

variable "cluster_arn" {
  description = "ECS cluster ARN"
}

variable "security_group_ids" {
  description = "Security group IDs"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC ID"
}
