resource "null_resource" "build_server_image" {
  depends_on = [random_uuid.container]

  triggers = {
    localsecrets_etag = data.aws_s3_object.localsecrets.etag
    app_sha1          = local.app_sha1
    dockerfile_sha1   = local.dockerfile_sha1
  }

  provisioner "local-exec" {
    working_dir = "../../"
    command     = <<-EOT
      aws s3 cp s3://pep-configuration/${var.env}/localsecrets.py app/config/localsecrets.py
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
      docker build --platform linux/amd64 -t ${local.container_name} -f ./Dockerfile  .
      docker tag ${local.container_name} ${var.repository_url}:${local.container_name}
      docker push ${var.repository_url}:${local.container_name}
      rm -rf app/config/localsecrets.py
    EOT
  }
}
