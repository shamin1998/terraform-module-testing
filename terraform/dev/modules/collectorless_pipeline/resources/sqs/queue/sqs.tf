resource "aws_sqs_queue" "sqs_queue" {
  count = var.queue_create ? 1 : 0
  name  = var.queue_name

  visibility_timeout_seconds = var.visibility_timeout_seconds
}

resource "aws_sqs_queue_policy" "queue_policy" {
  count = var.queue_create ? 1 : 0
  queue_url = aws_sqs_queue.sqs_queue[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowSendMessage"
        Effect    = "Allow"
        Principal = "*"
        Action    = var.queuepolicy_actions
        Resource  = "${aws_sqs_queue.sqs_queue[0].arn}"
      }
    ]
  })
}

##############
####output####
##############

output "sqs_queue_url" {
  value = var.queue_create ? aws_sqs_queue.sqs_queue[0].id : null
}

output "sqs_queue_arn" {
  value = var.queue_create ? aws_sqs_queue.sqs_queue[0].arn : null
}