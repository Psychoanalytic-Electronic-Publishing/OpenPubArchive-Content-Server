locals {
  config_sha1                   = sha1(join("", [for f in fileset(path.cwd, "../../app/config/*") : filesha1(f)]))
  libs_sha1                     = sha1(join("", [for f in fileset(path.cwd, "../../app/libs/*") : filesha1(f)]))
  opasDataLoader_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataLoader/*") : filesha1(f)]))
  opasDataUpdateStat_sha1       = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataUpdateStat/*") : filesha1(f)]))
  opasEndnoteExport_sha1        = sha1(join("", [for f in fileset(path.cwd, "../../app/opasEndnoteExport/*") : filesha1(f)]))
  opasGoogleMetadataExport_sha1 = sha1(join("", [for f in fileset(path.cwd, "../../app/opasGoogleMetadataExport/*") : filesha1(f)]))
  opasPushSettings_sha1         = sha1(join("", [for f in fileset(path.cwd, "../../app/opasPushSettings/*") : filesha1(f)]))
  opasSiteMapper_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasSiteMapper/*") : filesha1(f)]))
  lambda_sha1                   = sha1(join("", [for f in fileset(path.cwd, "../../lambda/data-utility/*") : filesha1(f)]))
  dockerfile_sha1               = filesha1("../../lambda/Dockerfile")
  name                          = "${var.stack_name}-data-utility-${var.env}"
}


resource "null_resource" "build_data_lambda_image" {
  triggers = {
    config_sha1                   = local.config_sha1
    libs_sha1                     = local.libs_sha1
    opasDataLoader_sha1           = local.opasDataLoader_sha1
    opasDataUpdateStat_sha1       = local.opasDataUpdateStat_sha1
    opasEndnoteExport_sha1        = local.opasEndnoteExport_sha1
    opasGoogleMetadataExport_sha1 = local.opasGoogleMetadataExport_sha1
    opasPushSettings_sha1         = local.opasPushSettings_sha1
    opasSiteMapper_sha1           = local.opasSiteMapper_sha1
    lambda_sha1                   = local.lambda_sha1
    dockerfile_sha1               = local.dockerfile_sha1
  }

  provisioner "local-exec" {
    working_dir = "../../"
    command     = <<-EOT
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
      docker build --platform linux/amd64 -t ${local.name}-latest -f lambda/Dockerfile --build-arg LAMBDA_HANDLER_PATH=lambda/data-utility/index.py .
      docker tag ${local.name}-latest ${aws_ecr_repository.opas_repository.repository_url}:${local.name}-latest
      docker push ${aws_ecr_repository.opas_repository.repository_url}:${local.name}-latest
    EOT
  }
}

module "data_lambda" {
  depends_on = [null_resource.build_data_lambda_image]

  source = "terraform-aws-modules/lambda/aws"

  function_name  = local.name
  description    = "Execute OPAS data tools with configurable options"
  create_package = false

  image_uri    = "${aws_ecr_repository.opas_repository.repository_url}:${local.name}-latest"
  package_type = "Image"

  timeout     = 900
  memory_size = 1024

  vpc_subnet_ids         = data.aws_subnets.vpc.ids
  vpc_security_group_ids = var.security_group_ids
  attach_network_policy  = true

  environment_variables = {
    BUCKET = "pep-configuration"
  }

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

resource "aws_iam_role_policy" "s3_policy" {
  role = module.data_lambda.lambda_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
        ]
        Effect   = "Allow"
        Resource = "arn:aws:s3:::pep-configuration/*"
      },
    ]
  })
}

resource "null_resource" "deploy_lambda_package" {
  depends_on = [
    null_resource.build_data_lambda_image,
    module.data_lambda
  ]

  triggers = {
    config_sha1                   = local.config_sha1
    libs_sha1                     = local.libs_sha1
    opasDataLoader_sha1           = local.opasDataLoader_sha1
    opasDataUpdateStat_sha1       = local.opasDataUpdateStat_sha1
    opasEndnoteExport_sha1        = local.opasEndnoteExport_sha1
    opasGoogleMetadataExport_sha1 = local.opasGoogleMetadataExport_sha1
    opasPushSettings_sha1         = local.opasPushSettings_sha1
    opasSiteMapper_sha1           = local.opasSiteMapper_sha1
    lambda_sha1                   = local.lambda_sha1
    dockerfile_sha1               = local.dockerfile_sha1
  }

  provisioner "local-exec" {
    command = "aws lambda update-function-code --function-name ${module.data_lambda.lambda_function_name} --image-uri ${aws_ecr_repository.opas_repository.repository_url}:${local.name}-latest"
  }
}
