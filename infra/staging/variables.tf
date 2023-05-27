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

variable "security_group_ids" {
  description = "Security group ID"
  default     = ["sg-0a97fbfa3e8ac6431"]
}

variable "cors_origin" {
  description = "CORS origin"
  default     = "https://stage.pep-web.org"
}

variable "pads_root" {
  description = "Root domain for PaDS"
  default     = "https://stage-pads.pep-web.org"
}
