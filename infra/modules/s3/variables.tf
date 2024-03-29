variable "env" {
  description = "Environment name"
}

variable "stack_name" {
  description = "Root name for the stack"
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
}

variable "versioning" {
  description = "Enable versioning for the bucket"
  default     = false
}
