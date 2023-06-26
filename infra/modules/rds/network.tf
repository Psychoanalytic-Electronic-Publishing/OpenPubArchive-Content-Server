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

resource "aws_security_group" "db" {
  name = "${var.stack_name}-db-sg-${var.env}"

  vpc_id = var.vpc_id

  // GitLab Runner - To be deprecated
  ingress {
    description = "MySQL from GitLab"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [var.gitlab_runner_ip]
  }

  ingress {
    description     = "MySQL from server"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [var.server_security_group_id]
  }

  ingress {
    description     = "MySQL from data-utility"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [var.data_utility_group_id]
  }

  ingress {
    description = "MySQL from self"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "MySQL from PEP engineer"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = formatlist("%s/32", split(",", var.engineer_ips))
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name  = "${var.stack_name}-db-sg-${var.env}"
    stack = var.stack_name
    env   = var.env
  }
}
