resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.bucket_name

  lambda_function {
    lambda_function_arn = var.smartload_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".xml"
  }
}
