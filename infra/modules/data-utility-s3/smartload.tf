module "smartload" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.9.0"

  function_name           = "${var.stack_name}-smartload-handler-${var.env}"
  source_path             = "../../dataUtility/s3/smartload"
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

resource "aws_iam_role_policy" "smartload_lambda_policy" {
  role = module.smartload.lambda_role_name

  policy = local.policy
}


resource "aws_lambda_permission" "allow_smartload" {
  statement_id  = "${var.stack_name}-allow-samrtload-${var.env}"
  action        = "lambda:InvokeFunction"
  function_name = module.smartload.lambda_function_name
  principal     = "s3.amazonaws.com"
  source_arn    = data.aws_s3_bucket.pep_web_data.arn
}
