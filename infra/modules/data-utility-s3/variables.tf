variable "env" {
  description = "Environment name"
}

variable "stack_name" {
  description = "Root name for the stack"
}

variable "staging_state_machine_arn" {
  description = "ARN of the state machine to invoke"
}

variable "production_state_machine_arn" {
  description = "ARN of the state machine to invoke"
}
