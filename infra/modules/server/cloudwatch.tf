resource "aws_cloudwatch_log_group" "server" {
  name = "${var.stack_name}-server-${var.env}"

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
