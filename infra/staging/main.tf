terraform {
  backend "s3" {
    key = "global/s3/opas-stage.tfstate"
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
  bucket_name = "pep-web-reports-staging"
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

  stack_name             = var.stack_name
  env                    = var.env
  account_id             = var.account_id
  aws_region             = var.aws_region
  repository_url         = module.ecr.repository_url
  repository_name        = module.ecr.repository_name
  ecr_execution_role_arn = module.ecr.ecr_execution_role_arn
  cluster_arn            = module.ecs.cluster_arn
  vpc_id                 = module.vpc.vpc_id
  cluster_name           = module.ecs.cluster_name
  api_domain             = "stage-api.pep-web.org"
  instance_cpu           = "256"
  instance_memory        = "1024"
  build_id               = var.build_id
}

module "database" {
  source = "../modules/rds"

  stack_name               = var.stack_name
  env                      = var.env
  instance_class           = "db.serverless"
  username                 = var.mysql_username
  password                 = var.mysql_password
  vpc_id                   = module.vpc.vpc_id
  data_utility_group_id    = module.data_utility.security_group_id
  server_security_group_id = module.server.security_group_id
  availability_zone        = "us-east-1f"
  pads_security_group_id   = "631911044226/sg-082ec49ff5d9e76cb"
  pads_ips                 = ["54.211.127.208/32"]
  min_capacity             = 0.5
  max_capacity             = 1
  instance_count           = 1
  backup_retention_period  = 7
  skip_final_snapshot      = true
  deletion_protection      = false
}

module "s3" {
  source = "../modules/s3"

  stack_name  = var.stack_name
  env         = var.env
  bucket_name = "pep-web-live-data-staging"
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
  instance_cpu             = "1024"
  instance_memory          = "2048"
  build_id                 = var.build_id
}
