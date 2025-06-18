variable "env" {
  description = "Environment name"
}

variable "stack_name" {
  description = "Root name for the stack"
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
}

variable "queue_arn" {
  description = "ARN of the SQS queue for S3 notifications"
}