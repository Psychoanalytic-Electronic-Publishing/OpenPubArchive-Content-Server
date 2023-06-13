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
