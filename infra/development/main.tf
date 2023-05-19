terraform {
  backend "s3" {
    key = "global/s3/opas-dev.tfstate"
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

  stack_name     = var.stack_name
  env            = var.env
  account_id     = var.account_id
  aws_region     = var.aws_region
  repository_url = module.ecr.repository_url
}

module "data-lambda" {
  source = "../modules/data-lambda"

  stack_name         = var.stack_name
  env                = var.env
  account_id         = var.account_id
  aws_region         = var.aws_region
  vpc_ids            = var.vpc_ids
  security_group_ids = var.security_group_ids
  repository_url     = module.ecr.repository_url
}
