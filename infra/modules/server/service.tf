resource "aws_ecs_task_definition" "server" {
  depends_on = [null_resource.build_server_image]

  family = "${var.stack_name}-server-${var.env}"

  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  execution_role_arn       = var.ecr_execution_role_arn

  cpu    = "1024"
  memory = "2048"

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
          awslogs-group         = aws_cloudwatch_log_group.server.name
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

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
}

resource "aws_ecs_service" "server" {
  name            = "${var.stack_name}-server-${var.env}"
  cluster         = var.cluster_arn
  task_definition = aws_ecs_task_definition.server.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = var.security_group_ids
    assign_public_ip = true
  }

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
