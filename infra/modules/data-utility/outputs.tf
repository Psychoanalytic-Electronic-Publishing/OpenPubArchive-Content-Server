output "state_machine_arn" {
  value = module.step_function.state_machine_arn
}

output "security_group_id" {
  value = aws_security_group.data_utility.id
}

output "queue_arn" {
  value = aws_sqs_queue.data_utility.arn
}
