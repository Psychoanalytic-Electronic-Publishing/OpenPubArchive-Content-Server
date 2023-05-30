module "execute_task_file" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.9.0"

  function_name           = "${var.stack_name}-execute-task-file-handler-${var.env}"
  source_path             = "../../dataUtility/s3/taskFile"
  handler                 = "index.handler"
  runtime                 = "python3.8"
  ignore_source_code_hash = true

  environment_variables = {
    STATE_MACHINE_ARN = var.state_machine_arn
  }

  tags = {
    stage = var.env
    stack = var.stack_name
  }
}

resource "aws_lambda_permission" "allow_execute_task_file" {
  statement_id  = "${var.stack_name}-allow-task-file-${var.env}"
  action        = "lambda:InvokeFunction"
  function_name = module.execute_task_file.lambda_function_name
  principal     = "s3.amazonaws.com"
  source_arn    = data.aws_s3_bucket.pep_web_live_data.arn
}

resource "aws_iam_role_policy" "start_task_lambda_policy" {
  role = module.execute_task_file.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
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
