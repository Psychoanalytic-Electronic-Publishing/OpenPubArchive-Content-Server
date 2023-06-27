data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
}

resource "aws_security_group" "data_utility" {
  name   = "${var.stack_name}-data-utility-sg-${var.env}"
  vpc_id = var.vpc_id

  ingress {
    description = "All ports from self"
    from_port   = 0
    to_port     = 0
    protocol    = "tcp"
    self        = true
  }


  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name  = "${var.stack_name}-data-utility-sg-${var.env}"
    stack = var.stack_name
    env   = var.env
  }
}
