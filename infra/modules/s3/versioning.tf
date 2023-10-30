resource "aws_s3_bucket_versioning" "versioning" {
  count = var.versioning ? 1 : 0

  bucket = aws_s3_bucket.pep_web_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "versioning-bucket-config" {
  count = var.versioning ? 1 : 0

  # Must have bucket versioning enabled first
  depends_on = [aws_s3_bucket_versioning.versioning]

  bucket = aws_s3_bucket.pep_web_data.id

  rule {
    id = "noncurrent-versions"


    noncurrent_version_expiration {
      noncurrent_days = 14
    }

    status = "Enabled"
  }
}
