resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.pep_web_data.id
  versioning_configuration {
    status = "Enabled"
  }
}
