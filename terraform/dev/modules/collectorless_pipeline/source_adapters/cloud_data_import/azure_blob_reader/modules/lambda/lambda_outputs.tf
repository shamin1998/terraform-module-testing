output "function_name" {
  value = aws_lambda_function.azure_blob_transfer_lambda.function_name
}

output "function_arn" {
  value = aws_lambda_function.azure_blob_transfer_lambda.arn
}

output "iam_role_id" {
  value = aws_iam_role.lambda_iam_role.id
}