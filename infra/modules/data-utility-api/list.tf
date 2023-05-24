module "list_tasks_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.9.0"

  function_name           = "${var.stack_name}-list-tasks-handler-${var.env}"
  source_path             = "../../dataUtility/api"
  handler                 = "listTasks.handler"
  runtime                 = "python3.8"
  ignore_source_code_hash = true

  tags = {
    stage = var.env
    stack = var.stack_name
  }
}

resource "aws_lambda_permission" "allow_list_tasks" {
  statement_id  = "${var.stack_name}-allow-list-tasks-${var.env}"
  action        = "lambda:InvokeFunction"
  function_name = module.list_tasks_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api_gateway.execution_arn}/*/*/*"
}

locals {
  list_tasks_integration = {
    get = {
      x-amazon-apigateway-integration = {
        httpMethod           = "POST"
        payloadFormatVersion = "1.0"
        type                 = "AWS_PROXY"
        uri                  = module.list_tasks_lambda.lambda_function_invoke_arn
      }
    },
    options = local.options
  }
}
