data "aws_iam_policy_document" "lambda_service_policy" {
  statement {
    sid    = ""
    effect = "Allow"

    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_iam_role" {
    count = var.role == "" ? 1 : 0

    name               = "${var.function_name}_role"
    assume_role_policy = data.aws_iam_policy_document.lambda_service_policy.json
}

resource "aws_lambda_function" "lambda_function" {

    function_name = var.function_name

    filename         = var.filename
    source_code_hash = var.source_code_hash

    role    = coalesce(var.role, aws_iam_role.lambda_iam_role[0].arn)
    handler = var.handler
    runtime = var.runtime
    timeout = var.timeout
    layers = var.layers

    dynamic environment {
        for_each = [var.environment]

        content {
            variables = environment.value["variables"]
        }
    }
}

# module cloudwatch_logs {
#     count = var.create_logs ? 1 : 0

#     source = "../../cloudwatch"

#     lambda_log_group_params = { function_name = aws_lambda_function.lambda_function[0].function_name }

#     depends_on = [ aws_lambda_function.lambda_function[0] ]
# }