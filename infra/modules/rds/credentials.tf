resource "aws_secretsmanager_secret" "credentials" {
  name = "${var.stack_name}/rds-credentials/${var.env}"

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

locals {
  credentials = {
    username             = var.username
    password             = var.password
    engine               = "mysql"
    host                 = aws_db_instance.mysql.address
    port                 = aws_db_instance.mysql.port
    dbname               = aws_db_instance.mysql.db_name
    dbInstanceIdentifier = aws_db_instance.mysql.identifier
  }
}

resource "aws_secretsmanager_secret_version" "credentials" {
  secret_id     = aws_secretsmanager_secret.credentials.id
  secret_string = jsonencode(local.credentials)
}
