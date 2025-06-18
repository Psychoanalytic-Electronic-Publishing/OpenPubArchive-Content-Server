resource "aws_ecr_repository" "opas_repository" {
  name                 = "${var.stack_name}-repository-${var.env}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }
}

resource "aws_ecr_lifecycle_policy" "opas_policy" {
  repository = aws_ecr_repository.opas_repository.name

  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Keep last 10 server images",
            "selection": {
                "tagStatus": "tagged",
                "tagPrefixList": ["server-"],
                "countType": "imageCountMoreThan",
                "countNumber": 10
            },
            "action": {
                "type": "expire"
            }
        },
        {
            "rulePriority": 2,
            "description": "Keep last 10 solr images",
            "selection": {
                "tagStatus": "tagged",
                "tagPrefixList": ["solr-"],
                "countType": "imageCountMoreThan",
                "countNumber": 10
            },
            "action": {
                "type": "expire"
            }
        },
        {
            "rulePriority": 3,
            "description": "Keep last 10 data-utility images",
            "selection": {
                "tagStatus": "tagged",
                "tagPrefixList": ["data-utility-"],
                "countType": "imageCountMoreThan",
                "countNumber": 10
            },
            "action": {
                "type": "expire"
            }
        },
        {
            "rulePriority": 4,
            "description": "Expire untagged images older than 1 day",
            "selection": {
                "tagStatus": "untagged",
                "countType": "sinceImagePushed",
                "countUnit": "days",
                "countNumber": 1
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}
