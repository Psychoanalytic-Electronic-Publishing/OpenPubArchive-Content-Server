resource "aws_ecs_task_definition" "solr" {
  depends_on = [null_resource.build_solr_image]

  family = "${var.stack_name}-solr-${var.env}"

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
        },
        {
          containerPort = 8983
          hostPort      = 8983
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.solr.name
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

resource "aws_ecs_service" "solr" {
  name            = "${var.stack_name}-solr-${var.env}"
  cluster         = var.cluster_arn
  task_definition = aws_ecs_task_definition.solr.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [aws_security_group.solr.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.solr.arn
    container_name   = "main"
    container_port   = 8983
  }

  #   lifecycle {
  #     ignore_changes = [desired_count]
  #   }

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
