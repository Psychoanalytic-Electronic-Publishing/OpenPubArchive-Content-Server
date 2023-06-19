variable "env" {
  description = "Environment name"
}

variable "stack_name" {
  description = "Root name for the stack"
}

variable "username" {
  description = "Username for the database"
  sensitive   = true
}

variable "password" {
  description = "Password for the database"
  sensitive   = true
}

variable "instance_class" {
  description = "Instance class for the database"
}

variable "vpc_id" {
  description = "VPC ID"
}

variable "gitlab_runner_ip" {
  description = "IP of the GitLab runner"
}

variable "server_security_group_id" {
  description = "Security group ID for the server"
}

variable "data_utility_group_id" {
  description = "Security group ID for the data-utility"
}

variable "availability_zone" {
  description = "Availability zone"
}
