resource "aws_lb" "server" {
  name               = "${var.stack_name}-server-alb-${var.env}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.server.id]
  subnets            = data.aws_subnets.private.ids
  idle_timeout       = 120

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

resource "aws_lb_target_group" "server" {
  name        = "${var.stack_name}-server-tg-${var.env}"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/v2/Api/Status/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 5
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
  }

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

resource "aws_lb_listener" "server_listener_http" {
  load_balancer_arn = aws_lb.server.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "server_listener_https" {
  load_balancer_arn = aws_lb.server.arn
  port              = "443"
  protocol          = "HTTPS"

  ssl_policy      = "ELBSecurityPolicy-2016-08"
  certificate_arn = "arn:aws:acm:us-east-1:547758924192:certificate/0ef7fa01-6a14-4342-a5cd-a3a55719b160"


  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.server.arn
  }
}
