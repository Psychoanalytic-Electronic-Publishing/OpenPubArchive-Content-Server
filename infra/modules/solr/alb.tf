resource "aws_lb" "solr" {
  name               = "${var.stack_name}-solr-alb-${var.env}"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.solr.id]
  subnets            = data.aws_subnets.private.ids
  idle_timeout       = 360

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

resource "aws_lb_target_group" "solr" {
  name        = "${var.stack_name}-solr-tg-${var.env}"
  port        = 8983
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/solr/admin/ping"
    port                = 8983
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 10
    matcher             = "200,401,403"
  }

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}


resource "aws_lb_listener" "solr_listener" {
  load_balancer_arn = aws_lb.solr.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.solr.arn
  }
}
