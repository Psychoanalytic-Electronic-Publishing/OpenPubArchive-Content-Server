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

module "ecr" {
  source = "../modules/ecr"

  stack_name = var.stack_name
  env        = var.env
}

module "data-lambda" {
  source = "../modules/data-lambda"

  stack_name = var.stack_name
  env        = var.env
  account_id = var.account_id
  aws_region = var.aws_region

  vpc_ids            = [aws_vpc.main.id]
  security_group_ids = var.security_group_ids
  repository_url     = module.ecr.repository_url
}
