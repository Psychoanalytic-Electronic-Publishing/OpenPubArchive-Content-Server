data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
}

resource "aws_security_group" "solr" {
  name        = "${var.stack_name}-solr-sg-${var.env}"
  description = "Allow HTTP inbound traffic and all outbound traffic"
  vpc_id      = var.vpc_id

  ingress {
    from_port = 8983
    to_port   = 8983
    protocol  = "tcp"
    self      = true
  }

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = distinct(concat([var.data_utility_group_id, var.server_security_group_id], var.additional_security_group_ids))
  }

  dynamic "ingress" {
    for_each = length(var.admin_ip_cidrs) > 0 ? toset(var.admin_ip_ports) : toset([])
    content {
      description = var.admin_ip_description
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = var.admin_ip_cidrs
    }
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "${var.stack_name}-solr-sg-${var.env}"
  }
}
