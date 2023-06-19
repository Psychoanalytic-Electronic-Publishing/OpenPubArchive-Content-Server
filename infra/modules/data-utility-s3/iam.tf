locals {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Effect   = "Allow"
        Resource = "${data.aws_s3_bucket.pep_web_live_data.arn}/*"
      },
      {
        Action = [
          "states:StartExecution",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}
