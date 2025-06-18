output "security_group_id" {
  description = "Security group ID for the server"
  value       = aws_security_group.server.id
}

output "task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.server_task_role.arn
}

output "ip_hmac_secret_arn" {
  description = "ARN of the IP HMAC secret"
  value       = data.aws_secretsmanager_secret.ip_hmac_secret.arn
}
