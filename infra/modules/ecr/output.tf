output "repository_url" {
  value = aws_ecr_repository.opas_repository.repository_url
}

output "repository_name" {
  value = aws_ecr_repository.opas_repository.name
}

output "ecr_execution_role_arn" {
  value = aws_iam_role.ecr_execution_role.arn
}
