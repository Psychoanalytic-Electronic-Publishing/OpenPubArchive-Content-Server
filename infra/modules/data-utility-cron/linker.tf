resource "aws_cloudwatch_event_rule" "weekly_data_linker" {
  count = var.env == "production" ? 1 : 0

  name                = "${var.stack_name}-weekly-data-linker-${var.env}"
  description         = "Run ${var.env} state machine every thursday at 03:00 UTC"
  schedule_expression = "cron(0 3 ? * 4 *)"
}

resource "aws_cloudwatch_event_target" "weekly_data_linker_target" {
  rule     = aws_cloudwatch_event_rule.nightly_data_pipeline.name
  role_arn = aws_iam_role.allow_cloudwatch_to_execute_role.arn
  arn      = var.state_machine_arn
  input = jsonencode({
    "task" : [
      [
        {
          "limitRam" : false,
          "directory" : "opasDataLoader",
          "utility" : "opasDataLinker",
          "args" : "--verbose --key ^*.* --unlinked"
        }
      ]
    ]
  })
}

