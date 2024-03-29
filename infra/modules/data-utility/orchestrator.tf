locals {
  definition_template = <<EOF
{
  "Comment": "State machine for orchestrating data utility",
  "StartAt": "Should Send Startup Email",
  "States": {
    "Should Send Startup Email": {
      "Type": "Choice",
      "Choices": [
        {
          "And": [
            {
              "Variable": "$.verbose",
              "IsPresent": true
            },
            {
              "Variable": "$.verbose",
              "BooleanEquals": true
            }
          ],
          "Next": "Startup Email"
        }
      ],
      "Default": "Batch"
    },
    "Startup Email": {
      "Type": "Task",
      "Resource": "${module.send_startup_email.lambda_function_arn}",
      "Parameters": {
        "task.$": "$.task",
        "verbose.$": "$.verbose",
        "executionArn.$": "$$.Execution.Id"
      },
      "Next": "Batch"
    },
    "Batch": {
      "Type": "Map",
      "ItemsPath": "$.task",
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
              "StartAt": "Limit RAM usage?",
              "States": {
                "Limit RAM usage?": {
                  "Type": "Choice",
                  "Choices": [
                    {
                      "Or": [
                        {
                          "Not": {
                            "Variable": "$.limitRam",
                            "IsPresent": true
                          }
                        },
                        {
                          "Variable": "$.limitRam",
                          "BooleanEquals": true
                        }
                      ],
                      "Next": "ECS RunTask (reduced RAM)"
                    }
                  ],
                  "Default": "ECS RunTask"
                },
                "ECS RunTask (reduced RAM)": {
                  "Type": "Task",
                  "Resource": "arn:aws:states:::ecs:runTask.sync",
                  "Parameters": {
                    "LaunchType": "FARGATE",
                    "Cluster": "${var.cluster_arn}",
                    "TaskDefinition": "${aws_ecs_task_definition.data_utility.arn}",
                    "NetworkConfiguration": {
                      "AwsvpcConfiguration": {
                        "Subnets": ${jsonencode(data.aws_subnets.private.ids)},
                        "SecurityGroups": [${jsonencode(aws_security_group.data_utility.id)}],
                        "AssignPublicIp": "ENABLED"
                      }
                    },
                    "Overrides": {
                      "ContainerOverrides": [
                        {
                          "Name": "main",
                          "Cpu": 512,
                          "Memory": 1024,
                          "Environment": [    
                            {
                              "Name": "UTILITY_DIRECTORY",
                              "Value.$": "$.directory"
                            },
                            {
                              "Name": "UTILITY_NAME",
                              "Value.$": "$.utility"
                            },
                            {
                              "Name": "UTILITY_ARGS",
                              "Value.$": "$.args"
                            }
                          ]
                        }
                      ]
                    }
                  },
                  "Catch": [
                    {
                      "ErrorEquals": [
                        "States.ALL"
                      ],
                      "Comment": "Catch all errors",
                      "Next": "Error Email",
                      "ResultPath": "$.error"
                    }
                  ],
                  "End": true
                },
                "ECS RunTask": {
                  "Type": "Task",
                  "Resource": "arn:aws:states:::ecs:runTask.sync",
                  "Parameters": {
                    "LaunchType": "FARGATE",
                    "Cluster": "${var.cluster_arn}",
                    "TaskDefinition": "${aws_ecs_task_definition.data_utility.arn}",
                    "NetworkConfiguration": {
                      "AwsvpcConfiguration": {
                        "Subnets": ${jsonencode(data.aws_subnets.private.ids)},
                        "SecurityGroups": [${jsonencode(aws_security_group.data_utility.id)}],
                        "AssignPublicIp": "ENABLED"
                      }
                    },
                    "Overrides": {
                      "ContainerOverrides": [
                        {
                          "Name": "main",
                          "Environment": [    
                            {
                              "Name": "UTILITY_DIRECTORY",
                              "Value.$": "$.directory"
                            },
                            {
                              "Name": "UTILITY_NAME",
                              "Value.$": "$.utility"
                            },
                            {
                              "Name": "UTILITY_ARGS",
                              "Value.$": "$.args"
                            }
                          ]
                        }
                      ]
                    }
                  },
                  "Catch": [
                    {
                      "ErrorEquals": [
                        "States.ALL"
                      ],
                      "Comment": "Catch all errors",
                      "Next": "Error Email",
                      "ResultPath": "$.error"
                    }
                  ],
                  "End": true
                },
                "Error Email": {
                  "Type": "Task",
                  "Resource": "${module.send_error_email.lambda_function_arn}",
                  "Parameters": {
                    "task.$": "$",
                    "executionArn.$": "$$.Execution.Id"
                  },
                  "End": true
                }
              }
            },
            "End": true
          }
        }
      },
      "Next": "Should Send Completion Email",
      "ResultPath": "$.batchResult",
      "MaxConcurrency": 1
    },
    "Should Send Completion Email": {
      "Type": "Choice",
      "Choices": [
        {
          "And": [
            {
              "Variable": "$.verbose",
              "IsPresent": true
            },
            {
              "Variable": "$.verbose",
              "BooleanEquals": true
            }
          ],
          "Next": "Completion Email"
        }
      ],
      "Default": "End"
    },
    "Completion Email": {
      "Type": "Task",
      "Parameters": {
        "executionArn.$": "$$.Execution.Id"
      },
      "Resource": "${module.send_completion_email.lambda_function_arn}",
      "End": true
    },
    "End": {
      "Type": "Succeed"
    }
  }
}
EOF

  dynamic_task_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecs:RunTask",
                "ecs:StopTask",
                "ecs:DescribeTasks"
            ],
            "Resource": "*"
        },
        {
          "Effect": "Allow",
          "Action": [
            "lambda:InvokeFunction"
          ],
          "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "events:PutTargets",
                "events:PutRule",
                "events:DescribeRule"
            ],
            "Resource": [
              "arn:aws:events:${var.aws_region}:${var.account_id}:rule/StepFunctionsGetEventsForECSTaskRule"
            ]
        },
        {
            "Action": [
                "iam:PassRole"
            ],
            "Resource": "*",
            "Effect": "Allow"
        }
    ]
}
EOF
}

module "step_function" {
  source = "terraform-aws-modules/step-functions/aws"

  name       = "${var.stack_name}-orchestrator-${var.env}"
  definition = local.definition_template

  attach_policy_json = true
  policy_json        = local.dynamic_task_policy


  type = "STANDARD"

  tags = {
    stack = var.stack_name
    env   = var.env
  }
}
