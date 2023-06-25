module "proxy" {
  source = "terraform-aws-modules/rds-proxy/aws"

  name                   = "${var.stack_name}-rds-proxy-${var.env}"
  iam_role_name          = "${var.stack_name}-proxy-role-${var.env}"
  vpc_subnet_ids         = data.aws_subnets.private.ids
  vpc_security_group_ids = [aws_security_group.db.id]


  auth = {
    "root" = {
      description = "MySQL root password"
      secret_arn  = aws_secretsmanager_secret.credentials.arn
    }
  }

  engine_family          = "MYSQL"
  target_db_instance     = true
  db_instance_identifier = aws_db_instance.mysql.id

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
