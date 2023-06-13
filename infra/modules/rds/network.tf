data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.stack_name}-subnet-group-${var.env}"
  subnet_ids = data.aws_subnets.private.ids

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
