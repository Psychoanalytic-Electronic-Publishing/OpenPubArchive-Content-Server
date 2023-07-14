resource "aws_iam_role" "proxy" {
  name = "${var.stack_name}-proxy-role-${var.env}"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "",
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "rds.amazonaws.com"
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

resource "aws_iam_role_policy" "proxy_policy" {
  role = aws_iam_role.proxy.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:Decrypt",
        ]
        Effect   = "Allow"
        Resource = "arn:aws:kms:*:*:key/*"
        Sid      = "DecryptSecrets"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "secretsmanager.us-east-1.amazonaws.com"
          }
        }
      },
      {
        Action = [
          "secretsmanager:ListSecrets",
          "secretsmanager:GetRandomPassword"
        ]
        Effect   = "Allow"
        Resource = "*"
        Sid      = "ListSecrets"
      },
      {
        Action = [
          "secretsmanager:ListSecretVersionIds",
          "secretsmanager:GetSecretValue",
          "secretsmanager:GetResourcePolicy",
          "secretsmanager:DescribeSecret"
        ]
        Effect   = "Allow"
        Resource = aws_secretsmanager_secret.credentials.arn
        Sid      = "GetSecrets"
      }
    ]
  })
}
