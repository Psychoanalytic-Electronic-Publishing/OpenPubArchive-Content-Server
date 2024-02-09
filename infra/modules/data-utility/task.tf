resource "aws_ecs_task_definition" "data_utility" {
  lifecycle {
    replace_triggered_by = [null_resource.build_data_utility_image]
  }

  depends_on = [null_resource.build_data_utility_image]

  family = "${var.stack_name}-data-utility-${var.env}"

  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  execution_role_arn       = var.ecr_execution_role_arn

  cpu    = "1024"
  memory = "8192"

  container_definitions = jsonencode([
    {
      name      = "main"
      image     = "${var.repository_url}:${local.container_name}"
      essential = true
      environment = [
        { NAME = "DRY_RUN_BUCKET", VALUE = var.dry_run_bucket },
        { NAME = "SNS_TOPIC_ARN", VALUE = aws_sns_topic.status_updates.arn },
      ]
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.data_utility.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    },
  ])

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
