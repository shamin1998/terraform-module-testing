# Defining AWS IAM Terraform resources

resource "aws_iam_policy" "lambda_secrets_policy" {
  name   = "lambda-secrets-policy-puuid-${var.pipeline_uuid}"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        Action : [
          "secretsmanager:GetSecretValue"
        ],
        Effect : "Allow",
        Resource : var.asm_secret_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_policy_attachment" {
  role = var.lambda_iam_role_id
  policy_arn = aws_iam_policy.lambda_secrets_policy.arn
}

resource "aws_iam_policy" "lambda_dynamodb_policy" {
  name   = "lambda-dynamodb-policy-puuid-${var.pipeline_uuid}"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        Action : [
            "dynamodb:DescribeTable",
            "dynamodb:Scan",
            "dynamodb:PutItem",
            "dynamodb:GetItem",
            "dynamodb:Query",
            "dynamodb:UpdateItem"

        ],
        Effect : "Allow",
        Resource : var.dynamodb_table_arn
      }
      # {
      #   Action : [
      #       "dynamodb:Query"
      #   ],
      #   Effect : "Allow",
      #   Resource : "${var.dynamodb_table_arn}/index/${var.dynamodb_table_sort_index}"
      # }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_policy_attachment" {
  role = var.lambda_iam_role_id
  policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}


resource "aws_iam_policy" "lambda_logging_policy" {
  name   = "lambda-logging-policy-puuid-${var.pipeline_uuid}"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        Action : [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect : "Allow",
        Resource : "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logging_policy_attachment" {
  role = var.lambda_iam_role_id
  policy_arn = aws_iam_policy.lambda_logging_policy.arn
}

resource "aws_iam_policy" "lambda_s3_policy" {
  name   = "lambda-s3-policy-puuid-${var.pipeline_uuid}"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        Action : "s3:PutObject",
        Effect : "Allow",
        Resource : "${var.s3_bucket_arn}/*"
      },
      {
        Action : "s3:ListBucket",
        Effect : "Allow",
        Resource : "${var.s3_bucket_arn}"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3_policy_attachment" {
  role = var.lambda_iam_role_id
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}

resource "aws_iam_policy" "lambda_sns_policy" {
  name   = "lambda-sns-policy-puuid-${var.pipeline_uuid}"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        Action : [
          "sns:Publish"
        ],
        Effect : "Allow",
        Resource : var.sns_topic_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sns_policy_attachment" {
  role = var.lambda_iam_role_id
  policy_arn = aws_iam_policy.lambda_sns_policy.arn
}
