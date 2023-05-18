
moved {
  from = module.ecs-temp
  to   = module.ecs.module.cluster
}

# locals {
#   config_sha1                   = sha1(join("", [for f in fileset(path.cwd, "../../app/config/*") : filesha1(f)]))
#   libs_sha1                     = sha1(join("", [for f in fileset(path.cwd, "../../app/libs/*") : filesha1(f)]))
#   opasDataLoader_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataLoader/*") : filesha1(f)]))
#   opasDataUpdateStat_sha1       = sha1(join("", [for f in fileset(path.cwd, "../../app/opasDataUpdateStat/*") : filesha1(f)]))
#   opasEndnoteExport_sha1        = sha1(join("", [for f in fileset(path.cwd, "../../app/opasEndnoteExport/*") : filesha1(f)]))
#   opasGoogleMetadataExport_sha1 = sha1(join("", [for f in fileset(path.cwd, "../../app/opasGoogleMetadataExport/*") : filesha1(f)]))
#   opasPushSettings_sha1         = sha1(join("", [for f in fileset(path.cwd, "../../app/opasPushSettings/*") : filesha1(f)]))
#   opasSiteMapper_sha1           = sha1(join("", [for f in fileset(path.cwd, "../../app/opasSiteMapper/*") : filesha1(f)]))
#   fargate_sha1                  = sha1(join("", [for f in fileset(path.cwd, "../../fargate/*") : filesha1(f)]))
#   name                          = "${var.stack_name}-data-lambda-${var.env}"
# }

# resource "random_uuid" "container" {
#   keepers = {
#     localsecrets_etag             = data.aws_s3_object.localsecrets.etag
#     config_sha1                   = local.config_sha1
#     libs_sha1                     = local.libs_sha1
#     opasDataLoader_sha1           = local.opasDataLoader_sha1
#     opasDataUpdateStat_sha1       = local.opasDataUpdateStat_sha1
#     opasEndnoteExport_sha1        = local.opasEndnoteExport_sha1
#     opasGoogleMetadataExport_sha1 = local.opasGoogleMetadataExport_sha1
#     opasPushSettings_sha1         = local.opasPushSettings_sha1
#     opasSiteMapper_sha1           = local.opasSiteMapper_sha1
#     fargate_sha1                  = local.fargate_sha1
#   }
# }

moved {
  from = random_uuid.container
  to   = module.data_utility.random_uuid.container
}

# locals {
#   container_name = "data-utility-${random_uuid.container.result}"
# }


# resource "null_resource" "build_data_utility_image" {
#   depends_on = [random_uuid.container]

#   triggers = {
#     localsecrets_etag             = data.aws_s3_object.localsecrets.etag
#     config_sha1                   = local.config_sha1
#     libs_sha1                     = local.libs_sha1
#     opasDataLoader_sha1           = local.opasDataLoader_sha1
#     opasDataUpdateStat_sha1       = local.opasDataUpdateStat_sha1
#     opasEndnoteExport_sha1        = local.opasEndnoteExport_sha1
#     opasGoogleMetadataExport_sha1 = local.opasGoogleMetadataExport_sha1
#     opasPushSettings_sha1         = local.opasPushSettings_sha1
#     opasSiteMapper_sha1           = local.opasSiteMapper_sha1
#     fargate_sha1                  = local.fargate_sha1
#   }

moved {
  from = null_resource.build_data_utility_image
  to   = module.data_utility.null_resource.build_data_utility_image
}

#   provisioner "local-exec" {
#     working_dir = "../../"
#     command     = <<-EOT
#       aws s3 cp s3://pep-configuration/${var.env}/localsecrets.py app/config/localsecrets.py
#       aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
#       docker build --platform linux/amd64 -t ${local.container_name} -f fargate/Dockerfile  .
#       docker tag ${local.container_name} ${module.ecr.repository_url}:${local.container_name}
#       docker push ${module.ecr.repository_url}:${local.container_name}
#       rm -rf app/config/localsecrets.py
#     EOT
#   }
# }

# ECR execution role
# resource "aws_iam_role" "ecr_execution_role" {
#   name = "${var.stack_name}-ecr-execution-role-${var.env}"

#   assume_role_policy = jsonencode({
#     "Version" : "2012-10-17",
#     "Statement" : [
#       {
#         "Sid" : "",
#         "Effect" : "Allow",
#         "Principal" : {
#           "Service" : "ecs-tasks.amazonaws.com"
#         },
#         "Action" : "sts:AssumeRole"
#       }
#     ]
#     }
#   )
# }

moved {
  from = aws_iam_role.ecr_execution_role
  to   = module.data_utility.aws_iam_role.ecr_execution_role
}

# resource "aws_iam_role_policy" "ecr_execution_policy" {
#   role = aws_iam_role.ecr_execution_role.name

#   policy = jsonencode({
#     "Version" : "2012-10-17",
#     "Statement" : [
#       {
#         "Effect" : "Allow",
#         "Action" : [
#           "ecr:GetAuthorizationToken",
#           "ecr:BatchCheckLayerAvailability",
#           "ecr:GetDownloadUrlForLayer",
#           "ecr:BatchGetImage",
#           "logs:CreateLogStream",
#           "logs:PutLogEvents"
#         ],
#         "Resource" : "*"
#       }
#     ]
#   })
# }

moved {
  from = aws_iam_role_policy.ecr_execution_policy
  to   = module.data_utility.aws_iam_role_policy.ecr_execution_policy
}

# resource "aws_cloudwatch_log_group" "data_utility" {
#   name = "${var.stack_name}-data-utility-${var.env}"

#   tags = {
#     stack = var.stack_name
#     env   = var.env
#   }
# }


moved {
  from = aws_cloudwatch_log_group.data_utility
  to   = module.data_utility.aws_cloudwatch_log_group.data_utility
}

# resource "aws_ecs_task_definition" "data_utility" {
#   depends_on = [null_resource.build_data_utility_image]

#   family = "${var.stack_name}-data-utility-${var.env}"

#   requires_compatibilities = ["FARGATE"]
#   network_mode             = "awsvpc"
#   execution_role_arn       = aws_iam_role.ecr_execution_role.arn

#   cpu    = ".5 vCPU"
#   memory = "1 GB"

#   container_definitions = jsonencode([
#     {
#       name      = "main"
#       image     = "${module.ecr.repository_url}:${local.container_name}"
#       essential = true
#       portMappings = [
#         {
#           containerPort = 80
#           hostPort      = 80
#         }
#       ]
#       logConfiguration = {
#         logDriver = "awslogs"
#         options = {
#           awslogs-group         = aws_cloudwatch_log_group.data_utility.name
#           awslogs-region        = var.aws_region
#           awslogs-stream-prefix = "ecs"
#         }
#       }
#     },
#   ])

#   tags = {
#     stack = var.stack_name
#     env   = var.env
#   }
# }

moved {
  from = aws_ecs_task_definition.data_utility
  to   = module.data_utility.aws_ecs_task_definition.data_utility
}
