resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.bucket_name

  queue {
    queue_arn     = var.queue_arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".xml"
  }
}
