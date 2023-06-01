data "aws_s3_bucket" "pep_web_live_data" {
  bucket = "pep-web-live-data"
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = data.aws_s3_bucket.pep_web_live_data.id

  lambda_function {
    lambda_function_arn = module.execute_task_file.lambda_function_arn_static
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".json"
    filter_prefix       = "run_${var.env}"
  }
}
