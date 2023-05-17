resource "null_resource" "build_data_lambda_image" {
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
    lambda_sha1                   = local.lambda_sha1
    dockerfile_sha1               = local.dockerfile_sha1
  }

  provisioner "local-exec" {
    working_dir = "../../"
    command     = <<-EOT
      aws s3 cp s3://pep-configuration/${var.env}/localsecrets.py app/config/localsecrets.py
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
      docker build --platform linux/amd64 -t ${local.container_name} -f lambda/Dockerfile --build-arg LAMBDA_HANDLER_PATH=lambda/data-utility/index.py .
      docker tag ${local.container_name} ${var.repository_url}:${local.container_name}
      docker push ${var.repository_url}:${local.container_name}
      rm -rf app/config/localsecrets.py
    EOT
  }
}

module "data_lambda" {
  depends_on = [null_resource.build_data_lambda_image]

  source = "terraform-aws-modules/lambda/aws"

  function_name  = local.name
  description    = "Execute OPAS data tools with configurable options"
  create_package = false

  image_uri    = "${var.repository_url}:${local.container_name}"
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
