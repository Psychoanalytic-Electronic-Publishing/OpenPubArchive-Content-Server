resource "aws_rds_cluster" "aurora_mysql" {
  cluster_identifier      = "${var.env}-v2-cluster"
  engine                  = "aurora-mysql"
  engine_mode             = "provisioned"
  engine_version          = "8.0.mysql_aurora.3.08.1"
  database_name           = "opascentral"
  master_username         = var.username
  master_password         = var.password
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  
  serverlessv2_scaling_configuration {
    max_capacity = var.max_capacity
    min_capacity = var.min_capacity
  }
  
  backup_retention_period    = var.backup_retention_period
  preferred_backup_window    = var.preferred_backup_window
  preferred_maintenance_window = var.preferred_maintenance_window
  
  skip_final_snapshot        = var.skip_final_snapshot
  final_snapshot_identifier  = var.skip_final_snapshot ? null : "${var.env}-final-snapshot-${replace(timestamp(), ":", "-")}"
  deletion_protection        = var.deletion_protection
  copy_tags_to_snapshot      = false  # Match current production state
  storage_encrypted          = true
  
  enabled_cloudwatch_logs_exports = []  # Match current production state
  
  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

resource "aws_rds_cluster_instance" "aurora_instance" {
  count = var.instance_count

  identifier             = "${var.env}-v2"
  cluster_identifier     = aws_rds_cluster.aurora_mysql.id
  instance_class         = "db.serverless"
  engine                 = aws_rds_cluster.aurora_mysql.engine
  engine_version         = aws_rds_cluster.aurora_mysql.engine_version
  
  performance_insights_enabled = false  # Match current production state
  monitoring_interval          = 60
  monitoring_role_arn          = aws_iam_role.rds_enhanced_monitoring.arn
  
  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "${var.stack_name}-rds-monitoring-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}