resource "aws_ecs_task_definition" "server" {
  depends_on = [null_resource.build_server_image]

  lifecycle {
    replace_triggered_by = [null_resource.build_server_image]
  }

  family = "${var.stack_name}-server-${var.env}"

  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  execution_role_arn       = var.ecr_execution_role_arn

  cpu    = var.instance_cpu
  memory = var.instance_memory

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

resource "aws_ecs_service" "server" {
  name            = "${var.stack_name}-server-${var.env}"
  cluster         = var.cluster_arn
  task_definition = aws_ecs_task_definition.server.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [aws_security_group.server.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.server.arn
    container_name   = "main"
    container_port   = 80
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
