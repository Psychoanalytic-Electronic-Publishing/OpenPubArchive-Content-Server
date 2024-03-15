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

variable "vpc_id" {
  description = "VPC ID"
}

variable "ecr_execution_role_arn" {
  description = "ECR execution role ARN"
}

variable "report_bucket" {
  description = "S3 bucket for data reports"
}
