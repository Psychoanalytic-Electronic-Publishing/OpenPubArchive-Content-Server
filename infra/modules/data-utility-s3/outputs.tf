output "smartload_lambda_arn" {
  value = module.smartload.lambda_function_arn
}

output "task_file_lambda_arn" {
  value = module.execute_task_file.lambda_function_arn
}
