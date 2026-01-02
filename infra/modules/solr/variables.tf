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

variable "repository_name" {
  description = "ECR repository name"
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

variable "server_security_group_id" {
  description = "Security group ID for the server"
}

variable "data_utility_group_id" {
  description = "Security group ID for the data-utility"
}

variable "additional_security_group_ids" {
  description = "Additional security group IDs allowed to access Solr (reworked NextJS app access)"
  type        = list(string)
  default     = []
}

variable "admin_ip_cidrs" {
  description = "Developer/admin CIDRs allowed to access Solr"
  type        = list(string)
  default     = []
}

variable "admin_ip_description" {
  description = "Description for developer/admin CIDR access"
  type        = string
  default     = "Developer access"
}

variable "admin_ip_ports" {
  description = "Ports to allow from developer/admin CIDRs"
  type        = list(number)
  default     = [80]
}

variable "instance_cpu" {
  description = "CPU units for the instance"
}

variable "instance_memory" {
  description = "Memory units for the instance"
}

variable "build_id" {
  description = "Unique build identifier"
  type        = string
}
