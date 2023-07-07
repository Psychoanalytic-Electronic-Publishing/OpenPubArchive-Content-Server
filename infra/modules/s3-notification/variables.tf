variable "env" {
  description = "Environment name"
}

variable "stack_name" {
  description = "Root name for the stack"
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
}

variable "smartload_arn" {
  description = "ARN of the smartload lambda function"
}