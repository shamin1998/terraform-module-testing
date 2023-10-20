output arn {
    value = aws_lambda_function.lambda_function.arn
}

output role_id {
    value = aws_iam_role.lambda_iam_role[0].id
}