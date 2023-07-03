resource "aws_cloudwatch_event_rule" "nightly_data_pipeline" {
  name                = "${var.stack_name}-nightly-data-pipeline-${var.env}"
  description         = "Run ${var.env} state machine everyday 23:00 UTC"
  schedule_expression = "cron(0 23 * * ? *)"
}

resource "aws_cloudwatch_event_target" "nightly_data_pipeline_target" {
  rule     = aws_cloudwatch_event_rule.nightly_data_pipeline.name
  role_arn = aws_iam_role.allow_cloudwatch_to_execute_role.arn
  arn      = var.state_machine_arn
  input = jsonencode([
    [
      {
        "directory" : "opasDataLoader",
        "utility" : "opasDataCleaner",
        "args" : "--nocheck"
      }
    ],
    [
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
          "args" : "--sub _PEPArchive --key ^A.* --smartload --verbose --nocheck --halfway"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^A.* --smartload --verbose --nocheck --halfway --reverse"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^[B-D].* --smartload --verbose --nocheck"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^[F-G].* --smartload --verbose --nocheck"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^H.* --smartload --verbose --nocheck"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^I.* --smartload --verbose --nocheck --halfway"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^I.* --smartload --verbose --nocheck --halfway --reverse"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^J.* --smartload --verbose --nocheck"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^K.* --smartload --verbose --nocheck"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^[L-O].* --smartload --verbose --nocheck"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^P.* --smartload --verbose --nocheck --halfway"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^P.* --smartload --verbose --nocheck --halfway --reverse"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^Q.* --smartload --verbose --nocheck"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^R.* --smartload --verbose --nocheck"
        },
        {
          "directory" : "opasDataLoader",
          "utility" : "opasDataLoader",
          "args" : "--sub _PEPArchive --key ^[S-Z].* --smartload --verbose --nocheck"
        }
      ]
    ]
    [
      {
        "directory" : "opasDataLoader",
        "utility" : "opasDataLinker",
        "args" : "--nightly"
      }
    ]
  ])
}
