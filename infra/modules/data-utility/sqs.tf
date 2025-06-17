# Dead Letter Queue
resource "aws_sqs_queue" "data_utility_dlq" {
  name = "data-utility-dlq-${var.env}"
  
  # DLQ configuration
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600  # 14 days
  receive_wait_time_seconds = 0
  visibility_timeout_seconds = 30
  
  # Enable server-side encryption
  sqs_managed_sse_enabled = true
  
  tags = {
    Name        = "${var.stack_name}-data-utility-dlq-${var.env}"
    Environment = var.env
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_sqs_queue" "data_utility" {
  name = "data-utility-sqs-${var.env}"
  
  # Standard queue configuration
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600  # 14 days
  receive_wait_time_seconds = 0
  visibility_timeout_seconds = 30
  
  # Enable server-side encryption
  sqs_managed_sse_enabled = true
  
  # Dead Letter Queue configuration
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.data_utility_dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = {
    Name        = "${var.stack_name}-data-utility-queue-${var.env}"
    Environment = var.env
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

# Policy to allow S3 to send messages to the queue
resource "aws_sqs_queue_policy" "data_utility" {
  queue_url = aws_sqs_queue.data_utility.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = "sqs:SendMessage"
        Resource = aws_sqs_queue.data_utility.arn
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = var.account_id
          }
        }
      }
    ]
  })
}