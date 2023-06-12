output "repository_url" {
  value = aws_ecr_repository.opas_repository.repository_url
}

output "ecr_execution_role_arn" {
  value = aws_iam_role.ecr_execution_role.arn
}
