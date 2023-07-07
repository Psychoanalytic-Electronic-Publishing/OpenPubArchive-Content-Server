resource "aws_s3_bucket" "pep_web_data" {
  bucket = var.bucket_name

  tags = {
    Bucket = var.bucket_name
    stack  = var.stack_name
    env    = var.env
  }
}
