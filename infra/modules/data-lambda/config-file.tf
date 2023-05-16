data "aws_s3_object" "localsecrets" {
  bucket = "pep-configuration"
  key    = "${var.env}/localsecrets.py"
}
