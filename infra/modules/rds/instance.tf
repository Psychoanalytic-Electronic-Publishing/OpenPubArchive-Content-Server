resource "aws_db_instance" "mysql" {
  allocated_storage     = 100
  max_allocated_storage = 250
  identifier            = "mysql-${var.env}"
  db_name               = "opascentral"
  engine                = "mysql"
  engine_version        = "8.0.28"
  instance_class        = "db.t3.micro"
  username              = "foo"
  password              = "foobarbaz"
  parameter_group_name  = "default.mysql8.0"
  skip_final_snapshot   = true
  db_subnet_group_name  = "default-vpc-0476e4a5a983d1193"

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
