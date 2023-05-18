resource "aws_ecs_task_definition" "data_utility" {
  depends_on = [null_resource.build_data_utility_image]

  family = "${var.stack_name}-data-utility-${var.env}"

  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  execution_role_arn       = aws_iam_role.ecr_execution_role.arn

  cpu    = "512"
  memory = "1024"

  container_definitions = jsonencode([
    {
      name      = "main"
      image     = "${var.repository_url}:${local.container_name}"
      essential = true
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
