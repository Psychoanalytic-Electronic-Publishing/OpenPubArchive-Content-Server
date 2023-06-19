resource "null_resource" "build_solr_image" {
  depends_on = [random_uuid.container]

  triggers = {
    dockerfile_sha1 = local.dockerfile_sha1
  }

  provisioner "local-exec" {
    working_dir = "../../solrCoreConfigurations"

    command = <<-EOT
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
      docker build --platform linux/amd64 -t ${local.container_name} -f ./Dockerfile  .
      docker tag ${local.container_name} ${var.repository_url}:${local.container_name}
      docker push ${var.repository_url}:${local.container_name}
    EOT
  }
}
