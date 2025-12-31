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
}

variable "stack_name" {
  description = "Root name for the stack"
  default     = "opas"
}

variable "cors_origin" {
  description = "CORS origin"
  default     = "https://stage.pep-web.org"
}

variable "pads_root" {
  description = "Root domain for PaDS"
  default     = "https://stage-pads.pep-web.org"
}

variable "mysql_username" {
  description = "Username for the database"
  sensitive   = true
}

variable "mysql_password" {
  description = "Password for the database"
  sensitive   = true
}


variable "build_id" {
  description = "Unique build identifier"
  type        = string
  default     = "local"
}

variable "admin_ip_cidrs" {
  description = "Developer/admin CIDR blocks for SG ingress"
  type        = list(string)
  default     = []
}

variable "admin_ip_description" {
  description = "Description for developer/admin CIDR ingress"
  type        = string
  default     = "Developer access"
}

variable "solr_admin_ip_ports" {
  description = "Ports to allow from developer/admin CIDRs to Solr"
  type        = list(number)
  default     = [80, 8983]
}
