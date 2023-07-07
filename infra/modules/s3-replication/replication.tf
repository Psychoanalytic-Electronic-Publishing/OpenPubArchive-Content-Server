
resource "aws_s3_bucket_replication_configuration" "replication" {
  depends_on = [aws_s3_bucket_versioning.source]

  role   = aws_iam_role.replication.arn
  bucket = var.source_bucket_name

  rule {
    id = "replicate-to-${var.destination_bucket_name}"

    status = "Enabled"

    destination {
      bucket        = data.aws_s3_bucket.destination.arn
      storage_class = "STANDARD"
    }
  }
}
