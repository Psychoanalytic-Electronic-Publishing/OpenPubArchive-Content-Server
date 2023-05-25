variable "env" {
  description = "Environment name"
}

variable "stack_name" {
  description = "Root name for the stack"
}

variable "cors_origin" {
  description = "CORS origin"
}

variable "state_machine_arn" {
  description = "ARN of the state machine to start"
}

variable "pads_root" {
  description = "Root domain for PaDS"
}
