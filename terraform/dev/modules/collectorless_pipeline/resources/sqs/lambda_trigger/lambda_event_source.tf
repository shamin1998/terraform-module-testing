resource "aws_lambda_event_source_mapping" "sqs_source_mapping" {
  event_source_arn = var.queue_arn
#   enabled          = true
  function_name    = var.lambda_function_arn
  batch_size       = var.batch_size
}