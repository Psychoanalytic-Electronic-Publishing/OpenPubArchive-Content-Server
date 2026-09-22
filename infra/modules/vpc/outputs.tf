output "vpc_id" {
  value = aws_vpc.main.id
}

# The VPC's main route table. No route table is declared in this module, so
# every subnet without an explicit association (the database subnets among
# them) routes through this one.
output "main_route_table_id" {
  value = aws_vpc.main.main_route_table_id
}
