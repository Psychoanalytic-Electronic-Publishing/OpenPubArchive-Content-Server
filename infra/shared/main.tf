terraform {
  backend "s3" {
    key = "global/s3/opas-shared.tfstate"
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

module "s3_replication" {
  source = "../modules/s3-replication"

  stack_name              = var.stack_name
  env                     = var.env
  source_bucket_name      = "pep-web-live-data"
  destination_bucket_name = "pep-web-live-data-staging"
}
