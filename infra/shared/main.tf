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

data "aws_s3_bucket" "pep_web_live_data" {
  bucket = "pep-web-live-data"
}

module "data_utility_s3" {
  source = "../modules/data-utility-s3"

  stack_name                = var.stack_name
  env                       = var.env
  staging_state_machine_arn = "arn:aws:states:us-east-1:547758924192:stateMachine:opas-orchestrator-staging"
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = data.aws_s3_bucket.pep_web_live_data.id

  lambda_function {
    lambda_function_arn = var.production_data_utility_s3_lambda
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".json"
    filter_prefix       = "run_production"
  }

  lambda_function {
    lambda_function_arn = var.staging_data_utility_s3_lambda
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".json"
    filter_prefix       = "run_staging"
  }

  lambda_function {
    lambda_function_arn = module.data_utility_s3.smartload_lambda_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".xml"
  }
}
