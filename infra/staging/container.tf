resource "aws_ecr_repository" "opas_repository" {
  name                 = "opas"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }
}

resource "aws_ecr_lifecycle_policy" "opas_policy" {
  repository = aws_ecr_repository.opas_repository.name

  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Expire images older than 14 days",
            "selection": {
                "tagStatus": "untagged",
                "countType": "sinceImagePushed",
                "countUnit": "days",
                "countNumber": 14
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}

locals {
  config_sha1     = sha1(join("", [for f in fileset(path.cwd, "../../app/config/*") : filesha1(f)]))
  libs_sha1       = sha1(join("", [for f in fileset(path.cwd, "../../app/libs/*") : filesha1(f)]))
  lambda_sha1     = sha1(join("", [for f in fileset(path.cwd, "../../lambda/test/*") : filesha1(f)]))
  dockerfile_sha1 = filesha1("../../lambda/Dockerfile")
}


resource "null_resource" "build_test_lambda_image" {
  triggers = {
    config_sha1     = local.config_sha1
    libs_sha1       = local.libs_sha1
    lambda_sha1     = local.lambda_sha1
    dockerfile_sha1 = local.dockerfile_sha1
  }

  provisioner "local-exec" {
    working_dir = "../../"
    command     = <<-EOT
      aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 547758924192.dkr.ecr.us-east-1.amazonaws.com
      docker build --platform linux/amd64 -t test:latest -f lambda/Dockerfile --build-art LAMBDA_HANDLER_PATH="lambda/test/index.py" .
      docker tag test:latest ${aws_ecr_repository.opas_repository.repository_url}:latest
      docker push ${aws_ecr_repository.opas_repository.repository_url}:latest
    EOT
  }
}

module "test_lambda" {
  depends_on = [null_resource.build_test_lambda_image]

  source = "terraform-aws-modules/lambda/aws"

  function_name = "test-lambda-with-container-image"
  description   = "My awesome lambda function"

  create_package = false

  image_uri    = "${aws_ecr_repository.opas_repository.repository_url}:latest"
  package_type = "Image"
}

resource "null_resource" "deploy_lambda_package" {
  depends_on = [
    null_resource.build_test_lambda_image,
    module.test_lambda
  ]

  triggers = {
    config_sha1     = local.config_sha1
    libs_sha1       = local.libs_sha1
    lambda_sha1     = local.lambda_sha1
    dockerfile_sha1 = local.dockerfile_sha1
  }

  provisioner "local-exec" {
    command = "aws lambda update-function-code --function-name ${module.test_lambda.lambda_function_name} --image-uri ${aws_ecr_repository.opas_repository.repository_url}:latest"
  }
}
