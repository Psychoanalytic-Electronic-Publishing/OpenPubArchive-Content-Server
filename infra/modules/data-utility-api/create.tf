module "create_task_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.9.0"

  function_name           = "${var.stack_name}-create-task-handler-${var.env}"
  source_path             = "../../dataUtility/api"
  handler                 = "createTask.handler"
  runtime                 = "python3.8"
  ignore_source_code_hash = true

  tags = {
    stage = var.env
    stack = var.stack_name
  }
}

resource "aws_lambda_permission" "allow_create_task" {
  statement_id  = "${var.stack_name}-allow-create-task-${var.env}"
  action        = "lambda:InvokeFunction"
  function_name = module.create_task_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api_gateway.execution_arn}/*/*/*"
}

locals {
  create_task_integration = {
    post = {
      x-amazon-apigateway-integration = {
        httpMethod           = "POST"
        payloadFormatVersion = "1.0"
        type                 = "AWS_PROXY"
        uri                  = module.create_task_lambda.lambda_function_invoke_arn
      }
    },
    options = local.options
  }
}
