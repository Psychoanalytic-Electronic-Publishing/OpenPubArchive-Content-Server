terraform {
  backend "s3" {
    key = "global/s3/opas-prod.tfstate"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.70"
    }
  }

  required_version = ">= 1.5.7"
}

provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "../modules/vpc"

  stack_name = var.stack_name
  env        = var.env
  cidr_block = "172.30.0.0/16"
}

module "ecr" {
  source = "../modules/ecr"

  stack_name = var.stack_name
  env        = var.env
}

module "ecs" {
  source = "../modules/ecs"

  stack_name = var.stack_name
  env        = var.env
}

module "s3_reports" {
  source = "../modules/s3"

  stack_name  = var.stack_name
  env         = var.env
  bucket_name = "pep-web-reports-production"
}

module "data_utility" {
  source = "../modules/data-utility"

  stack_name             = var.stack_name
  env                    = var.env
  account_id             = var.account_id
  aws_region             = var.aws_region
  repository_url         = module.ecr.repository_url
  repository_name        = module.ecr.repository_name
  cluster_arn            = module.ecs.cluster_arn
  vpc_id                 = module.vpc.vpc_id
  ecr_execution_role_arn = module.ecr.ecr_execution_role_arn
  report_bucket          = module.s3_reports.bucket_name
  build_id               = var.build_id

  depends_on = [module.server]
}


module "data_utility_api" {
  source = "../modules/data-utility-api"

  stack_name        = var.stack_name
  env               = var.env
  cors_origin       = var.cors_origin
  state_machine_arn = module.data_utility.state_machine_arn
  pads_root         = var.pads_root
}

module "data_utility_cron" {
  source = "../modules/data-utility-cron"

  stack_name        = var.stack_name
  env               = var.env
  state_machine_arn = module.data_utility.state_machine_arn
}

module "server" {
  source = "../modules/server"

  stack_name               = var.stack_name
  env                      = var.env
  account_id               = var.account_id
  aws_region               = var.aws_region
  repository_url           = module.ecr.repository_url
  repository_name          = module.ecr.repository_name
  ecr_execution_role_arn   = module.ecr.ecr_execution_role_arn
  cluster_arn              = module.ecs.cluster_arn
  vpc_id                   = module.vpc.vpc_id
  cluster_name             = module.ecs.cluster_name
  api_domain               = "api.pep-web.org"
  instance_cpu             = "2048"
  instance_memory          = "4096"
  autoscaling_min_capacity = 3
  autoscaling_max_capacity = 10
  build_id                 = var.build_id
}

module "database" {
  source = "../modules/rds"

  stack_name               = var.stack_name
  env                      = var.env
  instance_class           = "db.t3.medium" # Not used for Aurora Serverless v2
  username                 = var.mysql_username
  password                 = var.mysql_password
  vpc_id                   = module.vpc.vpc_id
  data_utility_group_id    = module.data_utility.security_group_id
  server_security_group_id = module.server.security_group_id
  # Reworked NextJS app access
  additional_security_group_ids = ["sg-07cca2c3dc7040bd8"]
  availability_zone             = "us-east-1f"
  pads_security_group_id        = "631911044226/sg-082ec49ff5d9e76cb"
  pads_ips                      = ["52.200.214.35/32", "34.202.154.34/32"]

  # Aurora Serverless v2 settings
  min_capacity            = 0.5   # AWS minimum is 0.5 (actual cluster has 0 - requires AWS support)
  max_capacity            = 128   # AWS maximum is 128 (actual cluster has 256 - requires AWS support)
  backup_retention_period = 1     # Match actual cluster configuration
  deletion_protection     = false # Match actual cluster configuration

  # Reworked NextJS app access
  proxy_additional_secret_arns = [
    "arn:aws:secretsmanager:us-east-1:547758924192:secret:rds-proxy/prod/app-EtSSCn",
    "arn:aws:secretsmanager:us-east-1:547758924192:secret:rds-proxy/prod/cms-uOpue0",
  ]
  admin_ip_cidrs       = var.admin_ip_cidrs
  admin_ip_description = var.admin_ip_description
}

module "s3" {
  source = "../modules/s3"

  stack_name  = var.stack_name
  env         = var.env
  bucket_name = "pep-web-live-data"
  versioning  = true
}

module "s3_videos" {
  source = "../modules/s3"

  stack_name  = var.stack_name
  env         = var.env
  bucket_name = "pep-video-originals"
  versioning  = false
}

module "data_utility_s3" {
  source = "../modules/data-utility-s3"

  stack_name        = var.stack_name
  env               = var.env
  state_machine_arn = module.data_utility.state_machine_arn
  bucket_name       = module.s3.bucket_name
  queue_arn         = module.data_utility.queue_arn
}

module "s3_notification" {
  depends_on = [module.s3, module.data_utility_s3]

  source = "../modules/s3-notification"

  stack_name  = var.stack_name
  env         = var.env
  bucket_name = module.s3.bucket_name
  queue_arn   = module.data_utility.queue_arn
}

module "solr" {
  source = "../modules/solr"

  stack_name               = var.stack_name
  env                      = var.env
  account_id               = var.account_id
  aws_region               = var.aws_region
  repository_url           = module.ecr.repository_url
  repository_name          = module.ecr.repository_name
  ecr_execution_role_arn   = module.ecr.ecr_execution_role_arn
  cluster_arn              = module.ecs.cluster_arn
  vpc_id                   = module.vpc.vpc_id
  data_utility_group_id    = module.data_utility.security_group_id
  server_security_group_id = module.server.security_group_id
  # Reworked NextJS app access
  additional_security_group_ids = ["sg-07cca2c3dc7040bd8"]
  admin_ip_cidrs                = var.admin_ip_cidrs
  admin_ip_description          = var.admin_ip_description
  admin_ip_ports                = var.solr_admin_ip_ports
  instance_cpu                  = "2048"
  instance_memory               = "16384"
  build_id                      = var.build_id
}
