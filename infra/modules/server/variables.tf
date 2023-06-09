variable "env" {
  description = "Environment name"
}

variable "stack_name" {
  description = "Root name for the stack"
}

variable "aws_region" {
  description = "AWS region"
}

variable "account_id" {
  description = "AWS account ID"
}

variable "repository_url" {
  description = "ECR repository URL"
}

variable "ecr_execution_role_arn" {
  description = "ECR execution role ARN"
}

variable "cluster_arn" {
  description = "ECS cluster ARN"
}

variable "vpc_id" {
  description = "VPC ID"
}

variable "cluster_name" {
  description = "ECS cluster name"
}

variable "api_domain" {
  description = "API domain"
}
