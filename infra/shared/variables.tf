variable "env" {
  description = "Environment name"
  default     = "shared"
}

variable "stack_name" {
  description = "Root name for the stack"
  default     = "opas"
}

variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "staging_data_utility_s3_lambda" {
  description = "Data utility S3 trigger function ARN for staging"
  default     = "arn:aws:lambda:us-east-1:547758924192:function:opas-execute-task-file-handler-staging"
}

variable "production_data_utility_s3_lambda" {
  description = "Data utility S3 trigger function ARN for production"
  default     = "arn:aws:lambda:us-east-1:547758924192:function:opas-execute-task-file-handler-production"
}

variable "staging_data_utility_smartload_lambda" {
  description = "Data utility S3 smartload function ARN for staging"
  default     = "arn:aws:lambda:us-east-1:547758924192:function:opas-smartload-handler-staging"
}
