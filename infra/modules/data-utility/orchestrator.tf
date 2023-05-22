locals {
  definition_template = <<EOF
{
  "Comment": "State machine for orchestrating data utility",
  "StartAt": "Batch",
  "States": {
    "Batch": {
      "Type": "Map",
      "ItemProcessor": {
        "ProcessorConfig": {
          "Mode": "INLINE"
        },
        "StartAt": "Job",
        "States": {
          "Job": {
            "Type": "Map",
            "ItemProcessor": {
              "ProcessorConfig": {
                "Mode": "INLINE"
              },
              "StartAt": "ECS RunTask",
              "States": {
                "ECS RunTask": {
                  "Type": "Task",
                  "Resource": "arn:aws:states:::ecs:runTask.sync",
                  "Parameters": {
                    "LaunchType": "FARGATE",
                    "Cluster": "${var.cluster_arn}",
                    "TaskDefinition": "${aws_ecs_task_definition.data_utility.arn}"
                  },
                  "End": true
                }
              }
            },
            "End": true
          }
        }
      },
      "End": true,
      "MaxConcurrency": 1
    }
  }
}
EOF
}

module "step_function" {
  source = "terraform-aws-modules/step-functions/aws"

  name       = "${var.stack_name}-orchestrator-${var.env}"
  definition = local.definition_template

  type = "STANDARD"

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
