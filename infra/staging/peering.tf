# VPC peering with the S-PRO PEP agentic-search environments.
#
# The agentic-search ETL (ECS Fargate in S-PRO's AWS account 907208926079,
# eu-central-1) reads opascentral over MySQL (3306). Aurora is private, so the
# path is a cross-account, inter-region VPC peering: S-PRO requests it from each
# of its environments, this side accepts and routes their CIDRs back.
#
# Two things worth knowing about this VPC before extending the pattern:
#   - the database subnets carry no explicit route-table association and fall
#     through to the VPC main route table, so the routes below apply to every
#     subnet in opas-staging-vpc, not only the database ones;
#   - opas-production-vpc uses the same 172.30.0.0/16, so a single remote VPC
#     can never peer with both staging and production. A production data path
#     needs its own design.

variable "pep_search_peerings" {
  description = "S-PRO PEP agentic-search environments peering into this VPC: the peering request they opened and their VPC CIDR"
  type = map(object({
    peering_connection_id = string
    cidr                  = string
  }))
  default = {
    dev = {
      peering_connection_id = "pcx-0f43dc6b853ee16d3"
      cidr                  = "10.60.0.0/16"
    }
    stage = {
      peering_connection_id = "pcx-0d82a1e0635039dd8"
      cidr                  = "10.61.0.0/16"
    }
  }
}

# Accept the requests. The requester side (S-PRO) owns the connection; a
# pending request expires after seven days if it is not accepted.
resource "aws_vpc_peering_connection_accepter" "pep_search" {
  for_each = var.pep_search_peerings

  vpc_peering_connection_id = each.value.peering_connection_id
  auto_accept               = true

  tags = {
    Name  = "${var.stack_name}-${var.env}-to-pep-search-${each.key}"
    stack = var.stack_name
    env   = var.env
  }
}

# Return route for each remote CIDR on the VPC main route table (see the note
# above on why it is the main table).
resource "aws_route" "pep_search" {
  for_each = var.pep_search_peerings

  route_table_id            = module.vpc.main_route_table_id
  destination_cidr_block    = each.value.cidr
  vpc_peering_connection_id = aws_vpc_peering_connection_accepter.pep_search[each.key].id
}
