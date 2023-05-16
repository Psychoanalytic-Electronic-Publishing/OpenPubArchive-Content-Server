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
