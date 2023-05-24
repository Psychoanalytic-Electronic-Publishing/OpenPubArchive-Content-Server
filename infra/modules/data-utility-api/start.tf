module "start_task_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.9.0"

  function_name           = "${var.stack_name}-start-task-handler-${var.env}"
  source_path             = "../../dataUtility/api"
  handler                 = "startTask.handler"
  runtime                 = "python3.8"
  ignore_source_code_hash = true

  tags = {
    stage = var.env
    stack = var.stack_name
  }
}

resource "aws_lambda_permission" "allow_start_task" {
  statement_id  = "${var.stack_name}-allow-start-task-${var.env}"
  action        = "lambda:InvokeFunction"
  function_name = module.start_task_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api_gateway.execution_arn}/*/*/*"
}

locals {
  start_task_integration = {
    post = {
      x-amazon-apigateway-integration = {
        httpMethod           = "POST"
        payloadFormatVersion = "1.0"
        type                 = "AWS_PROXY"
        uri                  = module.start_task_lambda.lambda_function_invoke_arn
      }
    },
    options = local.options
  }
}
