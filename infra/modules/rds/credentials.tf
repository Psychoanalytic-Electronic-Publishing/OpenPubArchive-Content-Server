resource "aws_secretsmanager_secret" "credentials" {
  name = "${var.stack_name}/rds-credentials/${var.env}"

  kms_key_id = "arn:aws:kms:us-east-1:547758924192:key/7b802a2f-38b3-40af-bca1-cdbc45ad8ceb"

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

locals {
  credentials = {
    dbInstanceIdentifier = var.env
    dbname               = aws_rds_cluster.aurora_mysql.database_name
    engine               = "mysql"
    host                 = aws_rds_cluster.aurora_mysql.endpoint
    password             = var.password
    port                 = aws_rds_cluster.aurora_mysql.port
    username             = var.username
  }
}

resource "aws_secretsmanager_secret_version" "credentials" {
  secret_id     = aws_secretsmanager_secret.credentials.id
  secret_string = jsonencode(local.credentials)
}
