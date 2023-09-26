resource "aws_cloudwatch_event_rule" "daily_archival" {
  count = var.env == "production" ? 1 : 0

  name                = "${var.stack_name}-daily-database-archival-${var.env}"
  description         = "Run database archival every day at 23:00 UTC"
  schedule_expression = "cron(0 23 * * ? *)"
}

resource "aws_cloudwatch_event_target" "daily_archival_target" {
  count = var.env == "production" ? 1 : 0

  rule     = aws_cloudwatch_event_rule.daily_archival[0].name
  role_arn = aws_iam_role.allow_cloudwatch_to_execute_role.arn
  arn      = var.state_machine_arn
  input = jsonencode({
    "task" : [
      [
        {
          "directory" : "opasDatabaseArchival",
          "utility" : "opasDatabaseArchival",
          "args" : "--table api_session_endpoints_not_logged_in --destination pep-stat-updater-archive-production"
        },
        {
          "directory" : "opasDatabaseArchival",
          "utility" : "opasDatabaseArchival",
          "args" : "--table api_session_endpoints --destination pep-stat-updater-archive-production"
        }
      ]
  ] })
}

