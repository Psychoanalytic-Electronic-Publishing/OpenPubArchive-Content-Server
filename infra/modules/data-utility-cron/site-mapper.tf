resource "aws_cloudwatch_event_rule" "weekly_site_map" {
  count = var.env == "production" ? 1 : 0

  name                = "${var.stack_name}-weekly-site-map-${var.env}"
  description         = "Run site mapper every Sunday at 15:00 UTC"
  schedule_expression = "cron(0 15 ? * SUN *)"
}

resource "aws_cloudwatch_event_target" "weekly_site_map_target" {
  count = var.env == "production" ? 1 : 0

  rule     = aws_cloudwatch_event_rule.weekly_site_map[0].name
  role_arn = aws_iam_role.allow_cloudwatch_to_execute_role.arn
  arn      = var.state_machine_arn
  input = jsonencode({
    "task" : [
      [
        {
          "directory" : "opasSiteMapper",
          "utility" : "opasSiteMapper",
          "args" : "--recordsperfile=2500 --maxrecords=300000 --bucket pep-web-google --clear",
          "limitRam" : false
        }
      ]
  ] })
}

