module "smartload" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.9.0"

  function_name           = "${var.stack_name}-smartload-handler-${var.env}"
  source_path             = "../../dataUtility/s3/smartload"
  handler                 = "index.handler"
  runtime                 = "python3.8"
  timeout                 = 10
  ignore_source_code_hash = true

  environment_variables = {
    STATE_MACHINE_ARN = var.state_machine_arn
  }

  tags = {
    stage = var.env
    stack = var.stack_name
  }
}

resource "aws_iam_role_policy" "smartload_lambda_policy" {
  role = module.smartload.lambda_role_name

  policy = local.policy
}

resource "aws_lambda_event_source_mapping" "smartload_sqs_trigger" {
  event_source_arn = var.queue_arn
  function_name    = module.smartload.lambda_function_name
  batch_size       = 50
  maximum_batching_window_in_seconds = 30
}

# Removed direct S3 permission - now using SQS trigger
