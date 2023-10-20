resource "aws_sns_topic" "transformation_trigger_sns_topic" {
    name = var.sns_topic_name
}

# resource "aws_sqs_queue" "sns_sub_queue" {
#   name = "sns-sub-queue"
# }

# resource "aws_sns_topic_subscription" "sns_lambda_subscription" {
#   topic_arn = aws_sns_topic.transformation_trigger_sns_topic.arn
#   protocol  = "lambda"
# #   endpoint  = aws_sqs_queue.sns_sub_queue.arn
#   endpoint = "arn:aws:lambda:us-east-1:116184061575:function:testAzureSDK"
# }

# resource "aws_lambda_permission" "with_sns" {
#   statement_id  = "AllowExecutionFromSNS"
#   action        = "lambda:InvokeFunction"
#   function_name = "testAzureSDK"
#   principal     = "sns.amazonaws.com"
#   source_arn    = aws_sns_topic.transformation_trigger_sns_topic.arn
# }