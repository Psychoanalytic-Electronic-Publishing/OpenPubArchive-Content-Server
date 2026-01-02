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

  ingress {
    description     = "MySQL from PaDS security group"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [var.pads_security_group_id]
  }

  ingress {
    description = "MySQL from PaDS IPs"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = var.pads_ips
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

  dynamic "ingress" {
    for_each = length(var.additional_security_group_ids) > 0 ? [1] : []
    content {
      description     = "MySQL from additional app security groups"
      from_port       = 3306
      to_port         = 3306
      protocol        = "tcp"
      security_groups = var.additional_security_group_ids
    }
  }

  dynamic "ingress" {
    for_each = length(var.admin_ip_cidrs) > 0 ? [1] : []
    content {
      description = var.admin_ip_description
      from_port   = 3306
      to_port     = 3306
      protocol    = "tcp"
      cidr_blocks = var.admin_ip_cidrs
    }
  }

  ingress {
    description = "MySQL from self"
    from_port   = 3306
    to_port     = 3306
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
    Name  = "${var.stack_name}-db-sg-${var.env}"
    stack = var.stack_name
    env   = var.env
  }
}
