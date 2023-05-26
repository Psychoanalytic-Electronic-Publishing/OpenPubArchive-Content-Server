resource "aws_api_gateway_rest_api" "api_gateway" {
  name        = "${var.stack_name}-orchestrator-${var.env}-api"
  description = "API Gateway for ${var.stack_name} orchestrator ${var.env}"
  tags = {
    stage = var.env
    stack = var.stack_name
  }
  body = jsonencode({
    openapi = "3.0.1"
    info = {
      title   = "example"
      version = "1.0"
    }
    paths = {
      "/start" = local.start_task_integration
      "/list"  = local.list_tasks_integration
      "/stop"  = local.stop_task_integration
    },
    components = {
      securitySchemes = {
        admin-auth = {
          type = "apiKey",
          name = "Authorization",
          in   = "header",
          x-amazon-apigateway-authorizer = {
            identitySource               = "method.request.header.Authorization",
            authorizerUri                = module.admin_auth_lambda.lambda_function_invoke_arn,
            authorizerResultTtlInSeconds = 300,
            type                         = "token",
            enableSimpleResponses        = false
          },
          x-amazon-apigateway-authtype = "Custom scheme with corporate claims"
        }
      }
    },
  })
}

resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api_gateway.id
  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.api_gateway.body))
  }
  lifecycle {
    create_before_destroy = true
  }
  stage_name = "v1"
}
