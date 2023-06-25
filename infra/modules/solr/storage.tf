module "efs" {
  source = "terraform-aws-modules/efs/aws"

  name = "${var.stack_name}-solr-efs-${var.env}"

  mount_targets = [
    for subnet_id in data.aws_subnets.private.ids : {
      subnet_id = subnet_id
    }
  ]

  security_group_vpc_id = var.vpc_id

  deny_nonsecure_transport           = false
  attach_policy                      = true
  bypass_policy_lockout_safety_check = false
  policy_statements = [
    {
      actions = [
        "elasticfilesystem:ClientRootAccess",
        "elasticfilesystem:ClientWrite",
        "elasticfilesystem:ClientMount"
      ]
      principals = [
        {
          type        = "AWS"
          identifiers = ["*"]
        }
      ]
    }
  ]

  security_group_rules = {
    vpc = {
      # relying on the defaults provdied for EFS/NFS (2049/TCP + ingress)
      description              = "NFS ingress from Solr ECS"
      source_security_group_id = aws_security_group.solr.id
    }
  }

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
