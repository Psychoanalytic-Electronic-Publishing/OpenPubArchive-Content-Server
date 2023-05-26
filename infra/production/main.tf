terraform {
  backend "s3" {
    key = "global/s3/opas-prod.tfstate"
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

  stack_name         = var.stack_name
  env                = var.env
  account_id         = var.account_id
  aws_region         = var.aws_region
  repository_url     = module.ecr.repository_url
  cluster_arn        = module.ecs.cluster_arn
  security_group_ids = var.security_group_ids
  vpc_id             = module.vpc.vpc_id
}

module "data_utility_api" {
  source = "../modules/data-utility-api"

  stack_name        = var.stack_name
  env               = var.env
  cors_origin       = var.cors_origin
  state_machine_arn = module.data_utility.state_machine_arn
  pads_root         = var.pads_root
}
