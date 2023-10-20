variable "queue_name" {
  type        = string
  description = "The name of the sqs queue "
  default     = "sqs-queue-webscale"
}
variable "queue_create" {
  type    = bool
  default = true
}
variable "queuepolicy_actions" {
  type    = list(string)
  default = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:CreateQueue"]
}

variable visibility_timeout_seconds {
  default = 900
}

/*
variable "queuepolicy_resource" {
  type    = string
  default = aws_sqs_queue.sqs_queue.arn
}
*/