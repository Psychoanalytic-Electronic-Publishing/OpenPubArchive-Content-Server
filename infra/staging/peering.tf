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
      peering_connection_id = "pcx-0e09c4e6fbc69ef60"
      cidr                  = "10.60.0.0/16"
    }
    stage = {
      peering_connection_id = "pcx-0e85a4529341c17cb"
      cidr                  = "10.61.0.0/16"
    }
  }
}

# Adopt the connections. The requester side (S-PRO) owns them, and a pending
# request expires after seven days: the first pair opened for this change died
# to exactly that while the PR waited for approval. The replacements above were
# accepted by hand the day they were opened, which stops the timer for good.
# auto_accept only fires while a connection is still pending-acceptance, so
# applying this against an already-active one just records it in state.
resource "aws_vpc_peering_connection_accepter" "pep_search" {
  for_each = var.pep_search_peerings

  vpc_peering_connection_id = each.value.peering_connection_id
  auto_accept               = true

  # Without this the data path does not work, even with the routes and the 3306
  # rule in place. staging-v2 is PubliclyAccessible, so the cluster endpoint
  # resolves to its public address for anyone outside this VPC -- including the
  # peered VPCs. Their traffic then matches 0.0.0.0/0 to the internet gateway
  # and never reaches the peering. Allowing DNS resolution from the remote VPC
  # makes the endpoint resolve to its 172.30.x private address over the
  # peering instead, which is the address the routes below actually serve.
  #
  # This has to be set on the accepter half, ours: the requester half controls
  # the opposite direction and was measured to have no effect here. Both
  # opas-staging-vpc DNS attributes are already enabled, so nothing outside
  # this resource changes.
  accepter {
    allow_remote_vpc_dns_resolution = true
  }

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
