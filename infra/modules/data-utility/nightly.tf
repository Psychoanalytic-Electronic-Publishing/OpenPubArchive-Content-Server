resource "aws_cloudwatch_event_rule" "nightly_data_pipeline" {
  name                = "${var.stack_name}-nightly-data-pipeline-${var.env}"
  description         = "Run ${var.env} state machine everyday 23:00 UTC"
  schedule_expression = "cron(0 23 * * ? *)"
}

data "aws_iam_policy_document" "allow_cloudwatch_to_execute_policy" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    principals {
      type = "Service"
      identifiers = [
        "states.amazonaws.com",
        "events.amazonaws.com"
      ]
    }
  }
}

resource "aws_iam_role" "allow_cloudwatch_to_execute_role" {
  name               = "${var.stack_name}-invoke-step-function-${var.env}"
  assume_role_policy = data.aws_iam_policy_document.allow_cloudwatch_to_execute_policy.json
}

resource "aws_iam_role_policy" "state_execution" {
  name = "state_execution_policy"
  role = aws_iam_role.allow_cloudwatch_to_execute_role.id

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1647307985962",
      "Action": [
        "states:StartExecution"
      ],
      "Effect": "Allow",
      "Resource": "${module.step_function.state_machine_arn}"
    }
  ]
}
EOF
}

resource "aws_cloudwatch_event_target" "nightly_data_pipeline_target" {
  rule     = aws_cloudwatch_event_rule.nightly_data_pipeline.name
  role_arn = aws_iam_role.allow_cloudwatch_to_execute_role.arn
  arn      = module.step_function.state_machine_arn
  input = jsonencode([
    [
      {
        "directory" : "opasDataLoader",
        "utility" : "opasDataCleaner",
        "args" : "--nocheck"
      }
    ],
    [
      {
        "directory" : "opasDataLoader",
        "utility" : "opasDataLoader",
        "args" : "--sub _PEPFree --smartload --verbose --nocheck"
      },
      {
        "directory" : "opasDataLoader",
        "utility" : "opasDataLoader",
        "args" : "--sub _PEPCurrent --smartload --verbose --nocheck"
      },
      {
        "directory" : "opasDataLoader",
        "utility" : "opasDataLoader",
        "args" : "--sub _PEPSpecial --smartload --verbose --nocheck"
      },
      {
        "directory" : "opasDataLoader",
        "utility" : "opasDataLoader",
        "args" : "--sub _PEPOffsite --smartload --verbose --nocheck"
      },
      {
        "directory" : "opasDataLoader",
        "utility" : "opasDataLoader",
        "args" : "--sub _PEPArchive/Videostreams --smartload --verbose --nocheck"
      },
    ],
    [
      {
        "directory" : "opasDataLoader",
        "utility" : "opasDataLinker",
        "args" : "--nightly"
      }
    ]
  ])
}

