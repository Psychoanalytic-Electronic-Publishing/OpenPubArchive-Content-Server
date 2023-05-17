resource "aws_vpc" "main" {
  cidr_block = var.cidr_block

  tags = {
    Name  = "${var.stack_name}-${var.env}-vpc"
    stack = var.stack_name
    env   = var.env
  }
}
