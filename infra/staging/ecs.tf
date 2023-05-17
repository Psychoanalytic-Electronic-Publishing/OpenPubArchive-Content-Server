module "ecs" {
  source = "terraform-aws-modules/ecs/aws"

  cluster_name = "${var.stack_name}-ecs-${var.env}"

  cluster_configuration = {
    execute_command_configuration = {
      logging = "OVERRIDE"
      log_configuration = {
        cloud_watch_log_group_name = "/aws/ecs/aws-ec2"
      }
    }
  }

  fargate_capacity_providers = {
    FARGATE = {
      default_capacity_provider_strategy = {
        weight = 50
      }
    }
    FARGATE_SPOT = {
      default_capacity_provider_strategy = {
        weight = 50
      }
    }
  }

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

data "aws_s3_object" "localsecrets" {
  bucket = "pep-configuration"
  key    = "${var.env}/localsecrets.py"
}


locals {
  config_sha1                   = sha1(join("", [for f in fileset(path.cwd, "../../app/config/*") : filesha1(f)]))
  libs_sha1                     = sha1(join("", [for f in fileset(path.cwd, "../../app/libs/*") : filesha1(f)]))
  opasDataLoader_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataLoader/*") : filesha1(f)]))
  opasDataUpdateStat_sha1       = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataUpdateStat/*") : filesha1(f)]))
  opasEndnoteExport_sha1        = sha1(join("", [for f in fileset(path.cwd, "../../app/opasEndnoteExport/*") : filesha1(f)]))
  opasGoogleMetadataExport_sha1 = sha1(join("", [for f in fileset(path.cwd, "../../app/opasGoogleMetadataExport/*") : filesha1(f)]))
  opasPushSettings_sha1         = sha1(join("", [for f in fileset(path.cwd, "../../app/opasPushSettings/*") : filesha1(f)]))
  opasSiteMapper_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasSiteMapper/*") : filesha1(f)]))
  dockerfile_sha1               = filesha1("../../fargate/Dockerfile")
  name                          = "${var.stack_name}-data-lambda-${var.env}"
}

resource "random_uuid" "container" {
  keepers = {
    localsecrets_etag             = data.aws_s3_object.localsecrets.etag
    config_sha1                   = local.config_sha1
    libs_sha1                     = local.libs_sha1
    opasDataLoader_sha1           = local.opasDataLoader_sha1
    opasDataUpdateStat_sha1       = local.opasDataUpdateStat_sha1
    opasEndnoteExport_sha1        = local.opasEndnoteExport_sha1
    opasGoogleMetadataExport_sha1 = local.opasGoogleMetadataExport_sha1
    opasPushSettings_sha1         = local.opasPushSettings_sha1
    opasSiteMapper_sha1           = local.opasSiteMapper_sha1
    dockerfile_sha1               = local.dockerfile_sha1
  }
}

locals {
  container_name = "data-utility-${random_uuid.container.result}"
}


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
    dockerfile_sha1               = local.dockerfile_sha1
  }

  provisioner "local-exec" {
    working_dir = "../../"
    command     = <<-EOT
      aws s3 cp s3://pep-configuration/${var.env}/localsecrets.py app/config/localsecrets.py
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
      docker build --platform linux/amd64 -t ${local.container_name} -f fargate/Dockerfile  .
      docker tag ${local.container_name} ${module.ecr.repository_url}:${local.container_name}
      docker push ${module.ecr.repository_url}:${local.container_name}
      rm -rf app/config/localsecrets.py
    EOT
  }
}
