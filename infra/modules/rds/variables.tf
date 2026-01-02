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


variable "server_security_group_id" {
  description = "Security group ID for the server"
}

variable "data_utility_group_id" {
  description = "Security group ID for the data-utility"
}

variable "availability_zone" {
  description = "Availability zone"
}


variable "pads_ips" {
  description = "IP of the PaDS instances"
  type        = list(string)
}


variable "pads_security_group_id" {
  description = "Security group ID for the PaDS"
}

variable "min_capacity" {
  description = "Minimum capacity for Aurora Serverless v2 in ACUs"
  type        = number
  default     = 0.5
}

variable "max_capacity" {
  description = "Maximum capacity for Aurora Serverless v2 in ACUs"
  type        = number
  default     = 128
}

variable "instance_count" {
  description = "Number of Aurora instances in the cluster"
  type        = number
  default     = 1
}

variable "proxy_additional_secret_arns" {
  description = "Additional Secrets Manager ARNs for RDS Proxy auth (reworked NextJS app access)"
  type        = list(string)
  default     = []
}

variable "additional_security_group_ids" {
  description = "Additional security group IDs allowed to access MySQL (reworked NextJS app access)"
  type        = list(string)
  default     = []
}

variable "admin_ip_cidrs" {
  description = "Developer/admin CIDRs allowed to access MySQL"
  type        = list(string)
  default     = []
}

variable "admin_ip_description" {
  description = "Description for developer/admin CIDR access"
  type        = string
  default     = "Developer access"
}

variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "preferred_backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "10:21-10:51"
}

variable "preferred_maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "wed:06:47-wed:07:17"
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on deletion"
  type        = bool
  default     = true
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}
