resource "aws_iam_role" "solr_task_role" {
  name = "${var.stack_name}-solr-task-role-${var.env}"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "",
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "ecs-tasks.amazonaws.com"
        },
        "Action" : "sts:AssumeRole"
      }
    ]
  })

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}

# Minimum permissions for ECS Exec (remote shell) sessions,
# plus session logging to the cluster's exec log group.
resource "aws_iam_role_policy" "solr_exec_policy" {
  name = "${var.stack_name}-solr-exec-policy-${var.env}"
  role = aws_iam_role.solr_task_role.id

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ],
        "Resource" : "*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "logs:DescribeLogStreams",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource" : "arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/aws/ecs/aws-ec2:*"
      }
    ]
  })
}
