resource "aws_s3_bucket_policy" "pep_web_live_data" {
  bucket = data.aws_s3_bucket.pep_web_live_data.id
  policy = data.aws_iam_policy_document.allow_datasync_from_another_account.json
}

data "aws_iam_policy_document" "allow_datasync_from_another_account" {
  statement {
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::872344130825:role/refarch/RoleCcpDataSync",
        "arn:aws:iam::914367642226:role/refarch/RoleCcpDataSync"
      ]
    }

    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucketMultipartUploads",
    ]

    resources = [
      "${data.aws_s3_bucket.pep_web_live_data.arn}"
    ]
  }

  statement {
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::872344130825:role/refarch/RoleCcpDataSync",
        "arn:aws:iam::914367642226:role/refarch/RoleCcpDataSync"
      ]
    }

    actions = [
      "s3:ListBucket"
    ]

    resources = [
      "${data.aws_s3_bucket.pep_web_live_data.arn}"
    ]
  }

  statement {
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::872344130825:role/refarch/RoleCcpDataSync",
        "arn:aws:iam::914367642226:role/refarch/RoleCcpDataSync"
      ]
    }

    actions = [
      "s3:PutObjectTagging",
      "s3:ListMultipartUploadParts",
      "s3:GetObjectTagging",
      "s3:GetObject",
      "s3:AbortMultipartUpload",
      "s3:GetObjectVersion",
      "s3:GetObjectVersionTagging"
    ]

    resources = [
      "${data.aws_s3_bucket.pep_web_live_data.arn}/_PEPFree/*(bEXP_ARCH1).xml",
      "${data.aws_s3_bucket.pep_web_live_data.arn}/_PEPArchive/*(bEXP_ARCH1).xml",
      "${data.aws_s3_bucket.pep_web_live_data.arn}/graphics/*(bEXP_ARCH1).xml",
    ]
  }
}
