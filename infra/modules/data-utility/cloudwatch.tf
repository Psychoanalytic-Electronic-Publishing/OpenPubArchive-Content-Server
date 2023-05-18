resource "aws_cloudwatch_log_group" "data_utility" {
  name = "${var.stack_name}-data-utility-${var.env}"

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
