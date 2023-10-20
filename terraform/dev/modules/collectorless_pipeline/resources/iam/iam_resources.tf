resource "aws_iam_policy" "lambda_secrets_policy" {
    count = var.lambda_iam_permissions.all || var.lambda_iam_permissions.allow_secrets ? 1 : 0

    name   = "${var.lambda_iam_role_id}-secrets-policy"
    policy = jsonencode({
        "Version" : "2012-10-17",
        "Statement" : [
        {
            Action : [
            "secretsmanager:GetSecretValue"
            ],
            Effect : "Allow",
            Resource : "*"  # var.lambda_logging_params.asm_secret_arn
        }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_policy_attachment" {
    count = var.lambda_iam_permissions.all || var.lambda_iam_permissions.allow_secrets ? 1 : 0

    role = var.lambda_iam_role_id
    policy_arn = aws_iam_policy.lambda_secrets_policy[0].arn
}

resource "aws_iam_policy" "lambda_dynamodb_policy" {
    count = var.lambda_iam_permissions.all || var.lambda_iam_permissions.allow_dynamodb ? 1 : 0

    name   = "${var.lambda_iam_role_id}-dynamodb-policy"
    policy = jsonencode({
        "Version" : "2012-10-17",
        "Statement" : [
        {
            Action : "dynamodb:*",      # ["dynamodb:DescribeTable", "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query", "dynamodb:UpdateItem" ],
            Effect : "Allow",
            Resource : "*"              # var.dynamodb_table_arn
        }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_policy_attachment" {
    count = var.lambda_iam_permissions.all || var.lambda_iam_permissions.allow_dynamodb ? 1 : 0
    
    role = var.lambda_iam_role_id
    policy_arn = aws_iam_policy.lambda_dynamodb_policy[0].arn
}


resource "aws_iam_policy" "lambda_logging_policy" {
    count = var.lambda_iam_permissions.all || var.lambda_iam_permissions.allow_logs ? 1 : 0

    name   = "${var.lambda_iam_role_id}-logging-policy"
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
    count = var.lambda_iam_permissions.all || var.lambda_iam_permissions.allow_logs ? 1 : 0

    role = var.lambda_iam_role_id
    policy_arn = aws_iam_policy.lambda_logging_policy[0].arn
}

resource "aws_iam_policy" "allow_lambda_access_s3" {
    count = var.lambda_iam_permissions.all || var.lambda_iam_permissions.allow_s3 ? 1 : 0

    name   = "${var.lambda_iam_role_id}-s3-policy"
    policy = jsonencode({
        "Version" : "2012-10-17",
        "Statement" : [
        {
            Action : "s3:*",   # var.allow_lambda_access_s3_params.actions,
            Effect : "Allow",
            Resource : "*"     # var.allow_lambda_access_s3_params.resources
        }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "allow_lambda_access_s3_attachment" {
    count = var.lambda_iam_permissions.all || var.lambda_iam_permissions.allow_s3 ? 1 : 0

    role = var.lambda_iam_role_id
    policy_arn = aws_iam_policy.allow_lambda_access_s3[0].arn
}

resource "aws_iam_policy" "lambda_sqs_policy" {
    count = var.lambda_iam_permissions.all || var.lambda_iam_permissions.allow_sqs ? 1 : 0

    name   = "${var.lambda_iam_role_id}-sqs-policy"
    policy = jsonencode({
        "Version" : "2012-10-17",
        "Statement" : [
        {
            Action : [
            "sqs:*"           # sqs:SendMessage
            ],
            Effect : "Allow",
            Resource : "*"      # var.sqs_queue_arn
        }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_policy_attachment" {
    count = var.lambda_iam_permissions.all || var.lambda_iam_permissions.allow_sqs ? 1 : 0
    
    role = var.lambda_iam_role_id
    policy_arn = aws_iam_policy.lambda_sqs_policy[0].arn
}
