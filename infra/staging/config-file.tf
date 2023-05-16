data "aws_s3_object" "localsecrets" {
  bucket = "pep-configuration"
  key    = "${var.env}/localsecrets.py"
}


resource "local_sensitive_file" "localsecrets" {
  content  = data.aws_s3_object.localsecrets.body
  filename = "../../app/config/localsecrets.py"
}
