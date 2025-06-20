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
  name   = "${var.stack_name}-db-sg-${var.env}"
  vpc_id = var.vpc_id

  # Outbound – allow everything
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

# GitLab Runner (to be deprecated)
resource "aws_security_group_rule" "db_mysql_gitlab_runner" {
  type              = "ingress"
  security_group_id = aws_security_group.db.id

  description = "MySQL from GitLab"
  from_port   = 3306
  to_port     = 3306
  protocol    = "tcp"

  cidr_blocks = [var.gitlab_runner_ip]
}

# PaDS security-group
resource "aws_security_group_rule" "db_mysql_pads_sg" {
  type              = "ingress"
  security_group_id = aws_security_group.db.id

  description = "MySQL from PaDS security group"
  from_port   = 3306
  to_port     = 3306
  protocol    = "tcp"

  source_security_group_id = var.pads_security_group_id
}

# PaDS IP allow-list
resource "aws_security_group_rule" "db_mysql_pads_ips" {
  for_each = toset(var.pads_ips)

  type              = "ingress"
  security_group_id = aws_security_group.db.id

  description = "MySQL from PaDS IPs"
  from_port   = 3306
  to_port     = 3306
  protocol    = "tcp"

  cidr_blocks = [each.key]
}

# Application server security-group
resource "aws_security_group_rule" "db_mysql_server_sg" {
  type              = "ingress"
  security_group_id = aws_security_group.db.id

  description = "MySQL from server"
  from_port   = 3306
  to_port     = 3306
  protocol    = "tcp"

  source_security_group_id = var.server_security_group_id
}

# Data-utility security-group
resource "aws_security_group_rule" "db_mysql_data_utility_sg" {
  type              = "ingress"
  security_group_id = aws_security_group.db.id

  description = "MySQL from data-utility"
  from_port   = 3306
  to_port     = 3306
  protocol    = "tcp"

  source_security_group_id = var.data_utility_group_id
}

# Self-reference
resource "aws_security_group_rule" "db_mysql_self" {
  type              = "ingress"
  security_group_id = aws_security_group.db.id

  description = "MySQL from self"
  from_port   = 3306
  to_port     = 3306
  protocol    = "tcp"

  self = true
}

# Engineer IPs
locals {
  engineer_cidrs = formatlist("%s/32", split(",", var.engineer_ips))
}

resource "aws_security_group_rule" "db_mysql_engineer_ips" {
  for_each = toset(local.engineer_cidrs)

  type              = "ingress"
  security_group_id = aws_security_group.db.id

  description = "MySQL from PEP engineer"
  from_port   = 3306
  to_port     = 3306
  protocol    = "tcp"

  cidr_blocks = [each.key]
}
