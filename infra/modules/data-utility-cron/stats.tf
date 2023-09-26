resource "aws_cloudwatch_event_rule" "weekly_stat_update" {
  count = var.env == "production" ? 1 : 0

  name                = "${var.stack_name}-weekly-stat-update-${var.env}"
  description         = "Run stat updater every Sunday at 15:00 UTC"
  schedule_expression = "cron(0 15 ? * SUN *)"
}

resource "aws_cloudwatch_event_target" "weekly_stat_update_target" {
  count = var.env == "production" ? 1 : 0

  rule     = aws_cloudwatch_event_rule.weekly_stat_update[0].name
  role_arn = aws_iam_role.allow_cloudwatch_to_execute_role.arn
  arn      = var.state_machine_arn
  input = jsonencode({
    "task" : [
      [
        {
          "directory" : "opasDataUpdateStat",
          "utility" : "opasDataUpdateStat",
          "args" : "--everything"
        }
      ]
  ] })
}

