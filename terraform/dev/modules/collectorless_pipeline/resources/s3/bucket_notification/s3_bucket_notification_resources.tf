resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.bucket_name

  dynamic lambda_function {
    for_each = var.lambda_function_arn != "" ? [var.lambda_function_arn] : []

    content {
        lambda_function_arn = var.lambda_function_arn
        events = var.events
        filter_prefix = var.filter_prefix
        filter_suffix = var.filter_suffix
    }
  }

  depends_on = [aws_lambda_permission.allow_bucket[0]]
}

output testing_out {
  value = var.bucket_name
}

resource "aws_lambda_permission" "allow_bucket" {
    count = var.notify == "lambda" ? 1 : 0

    statement_id  = "AllowLambdaInvocationFromS3Bucket"
    action        = "lambda:InvokeFunction"
    function_name = var.lambda_function_arn
    principal     = "s3.amazonaws.com"
    source_arn    = var.bucket_arn
}
