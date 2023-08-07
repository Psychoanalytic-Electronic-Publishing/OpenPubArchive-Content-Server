resource "aws_cloudwatch_log_group" "solr" {
  name = "${var.stack_name}-solr-${var.env}"

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
