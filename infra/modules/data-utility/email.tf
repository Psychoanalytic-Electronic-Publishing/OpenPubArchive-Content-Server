resource "aws_sns_topic" "status_updates" {
  name = "${var.stack_name}-status-updates-${var.env}"
}

module "send_status_email" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.9.0"

  function_name           = "${var.stack_name}-send-status-email-${var.env}"
  source_path             = "../../dataUtility/email"
  handler                 = "index.handler"
  runtime                 = "python3.8"
  ignore_source_code_hash = true

  environment_variables = {
    SNS_TOPIC_ARN = aws_sns_topic.status_updates.arn
  }

  tags = {
    stage = var.env
    stack = var.stack_name
  }
}


resource "aws_iam_role_policy" "send_status_email_lambda_policy" {
  role = module.send_status_email.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "states:GetExecutionHistory",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "sns:Publish"
        ],
        Effect   = "Allow",
        Resource = aws_sns_topic.status_updates.arn
      }
    ]
  })
}
