
resource "null_resource" "build_data_utility_image" {
  depends_on = [random_uuid.container]

  triggers = {
    localsecrets_etag             = data.aws_s3_object.localsecrets.etag
    config_sha1                   = local.config_sha1
    libs_sha1                     = local.libs_sha1
    opasDataLoader_sha1           = local.opasDataLoader_sha1
    opasDataUpdateStat_sha1       = local.opasDataUpdateStat_sha1
    opasEndnoteExport_sha1        = local.opasEndnoteExport_sha1
    opasGoogleMetadataExport_sha1 = local.opasGoogleMetadataExport_sha1
    opasPushSettings_sha1         = local.opasPushSettings_sha1
    opasSiteMapper_sha1           = local.opasSiteMapper_sha1
    fargate_sha1                  = local.fargate_sha1
  }

  provisioner "local-exec" {
    working_dir = "../../"
    command     = <<-EOT
      aws s3 cp s3://pep-configuration/${var.env}/localsecrets.py app/config/localsecrets.py
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
      docker build --platform linux/amd64 -t ${local.container_name} -f fargate/Dockerfile  .
      docker tag ${local.container_name} ${var.repository_url}:${local.container_name}
      docker push ${var.repository_url}:${local.container_name}
      rm -rf app/config/localsecrets.py
    EOT
  }
}
