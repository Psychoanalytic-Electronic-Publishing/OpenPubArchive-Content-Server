resource "aws_s3_bucket_versioning" "destination" {
  bucket = data.aws_s3_bucket.destination.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "source" {
  bucket = data.aws_s3_bucket.source.id
  versioning_configuration {
    status = "Enabled"
  }
}
