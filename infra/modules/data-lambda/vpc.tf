data "aws_subnets" "vpc" {
  filter {
    name   = "vpc-id"
    values = var.vpc_ids
  }
}
