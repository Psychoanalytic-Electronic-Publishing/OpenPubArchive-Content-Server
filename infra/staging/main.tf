terraform {
  backend "s3" {
    key = "global/s3/opas-stage.tfstate"
  }

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }

  required_version = ">= 1.2.0"
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

module "data_utility" {
  source = "../modules/data-utility"

  stack_name             = var.stack_name
  env                    = var.env
  account_id             = var.account_id
  aws_region             = var.aws_region
  repository_url         = module.ecr.repository_url
  cluster_arn            = module.ecs.cluster_arn
  security_group_ids     = var.security_group_ids
  vpc_id                 = module.vpc.vpc_id
  ecr_execution_role_arn = module.ecr.ecr_execution_role_arn
}

module "data_utility_api" {
  source = "../modules/data-utility-api"

  stack_name        = var.stack_name
  env               = var.env
  cors_origin       = var.cors_origin
  state_machine_arn = module.data_utility.state_machine_arn
  pads_root         = var.pads_root
}

module "data_utility_s3" {
  source = "../modules/data-utility-s3"

  stack_name        = var.stack_name
  env               = var.env
  state_machine_arn = module.data_utility.state_machine_arn
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
  ecr_execution_role_arn = module.ecr.ecr_execution_role_arn
  cluster_arn            = module.ecs.cluster_arn
  vpc_id                 = module.vpc.vpc_id
  cluster_name           = module.ecs.cluster_name
  api_domain             = "stage-api.pep-web.org"
  instance_cpu           = "256"
  instance_memory        = "1024"
}

module "database" {
  source = "../modules/rds"

  stack_name               = var.stack_name
  env                      = var.env
  instance_class           = "db.t3.micro"
  username                 = var.mysql_username
  password                 = var.mysql_password
  vpc_id                   = module.vpc.vpc_id
  data_utility_group_id    = var.security_group_ids[0]
  server_security_group_id = module.server.security_group_id
  gitlab_runner_ip         = "54.210.185.163/32"
  availability_zone        = "us-east-1f"
  engineer_ips             = var.engineer_ips
}
