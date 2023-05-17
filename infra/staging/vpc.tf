resource "aws_vpc" "main" {
  cidr_block = "172.30.0.0/16"

  tags = {
    Name  = "${var.stack_name}-${var.env}-vpc"
    stack = var.stack_name
    env   = var.env
  }
}
