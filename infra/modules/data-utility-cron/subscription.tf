resource "aws_cloudwatch_event_rule" "generate_subscription_update" {
  name                = "${var.stack_name}-generate-subscription-update-${var.env}"
  description         = "Generate a subscription update every Wednesday at 15:00 UTC"
  schedule_expression = "cron(0 15 ? * 4 *)"
}

resource "aws_cloudwatch_event_target" "generate_subscription_update_target" {
  rule     = aws_cloudwatch_event_rule.generate_subscription_update.name
  role_arn = aws_iam_role.allow_cloudwatch_to_execute_role.arn
  arn      = var.state_machine_arn
  input = jsonencode([
    [
      {
        "directory" : "opasDataLoader",
        "utility" : "opasDataLoader",
        "args" : "--nocheck --nofiles --whatsnewdays=7"
      }
    ]
  ])
}

