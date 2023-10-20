# AWS CloudWatch Terraform Resources
####################################

### Event Rules ###

resource "aws_cloudwatch_event_rule" "custom_rule" {
    description = "Creates an Event Rule from the `schedule_expression` or `event_pattern`"
    
    name = var.name
    
    schedule_expression = var.schedule_expression
    # event_pattern = var.event_pattern

    # # Optional variables
    # role_arn = var.role_arn
    # is_enabled = var.is_enabled

}

resource "aws_cloudwatch_event_target" "azure_blob_transfer_lambda_trigger_schedule" {
    rule = var.name
    arn = var.lambda_function_arn

    depends_on = [ aws_cloudwatch_event_rule.custom_rule ]
}

resource "aws_lambda_permission" "allow_cloudwatch_invoke_lambda" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = var.function_name
    principal = "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.custom_rule.arn
}


# resource "aws_cloudwatch_event_rule" "rate_x_minutes_rule" {
#     description = "Creates an Event Rule which triggers every ${var.rate_x_minutes_rule_params.x} minutes"

#     count = var.rate_x_minutes_rule_params.create ? 1 : 0
#     name = var.rate_x_minutes_rule_params.name
    
#     schedule_expression = "rate(${var.rate_x_minutes_rule_params.x} ${var.rate_x_minutes_rule_params.x == 1 ? "minute" : "minutes"})"
# }

# resource "aws_cloudwatch_event_rule" "cron_x_minutes_rule" {
#     description = "Creates an Event Rule which triggers every ${var.cron_x_minutes_rule_params.x} minutes"

#     count = var.cron_x_minutes_rule_params.create ? 1 : 0
#     name = var.cron_x_minutes_rule_params.name
    
#     schedule_expression = "cron(${var.cron_x_minutes_rule_params.x} ${var.cron_x_minutes_rule_params.x == 1 ? "minute" : "minutes"})"
# }

