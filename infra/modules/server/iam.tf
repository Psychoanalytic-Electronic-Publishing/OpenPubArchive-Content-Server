resource "aws_iam_role" "server_task_role" {
  name = "${var.stack_name}-server-task-role-${var.env}"

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

# Data sources for existing KMS key and secret
data "aws_secretsmanager_secret" "ip_hmac_secret" {
  name = "pep-web-ip-hmac-${var.env}"
}

resource "aws_iam_role_policy" "server_secrets_policy" {
  name = "${var.stack_name}-server-secrets-policy-${var.env}"
  role = aws_iam_role.server_task_role.id

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "secretsmanager:GetSecretValue"
        ],
        "Resource" : [
          data.aws_secretsmanager_secret.ip_hmac_secret.arn
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ],
        "Resource" : [
          "arn:aws:kms:us-east-1:547758924192:key/7b802a2f-38b3-40af-bca1-cdbc45ad8ceb"
        ]
      }
    ]
  })
}