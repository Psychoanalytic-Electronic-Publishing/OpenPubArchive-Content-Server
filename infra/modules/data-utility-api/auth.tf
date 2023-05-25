module "admin_auth_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.9.0"

  function_name           = "${var.stack_name}-admin-auth-handler-${var.env}"
  source_path             = "../../dataUtility/api/auth"
  handler                 = "index.handler"
  runtime                 = "python3.8"
  ignore_source_code_hash = true

  environment_variables = {
    PADS_ROOT = var.pads_root
  }

  tags = {
    stage = var.env
    stack = var.stack_name
  }
}

resource "aws_api_gateway_authorizer" "admin" {
  name           = "admin-auth"
  rest_api_id    = aws_api_gateway_rest_api.api_gateway.id
  authorizer_uri = module.admin_auth_lambda.lambda_function_invoke_arn
}


resource "aws_lambda_permission" "allow_admin_atuh" {
  statement_id  = "${var.stack_name}-allow-admin-auth-${var.env}"
  action        = "lambda:InvokeFunction"
  function_name = module.admin_auth_lambda.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api_gateway.execution_arn}/authorizers/${aws_api_gateway_authorizer.admin.id}"
}
