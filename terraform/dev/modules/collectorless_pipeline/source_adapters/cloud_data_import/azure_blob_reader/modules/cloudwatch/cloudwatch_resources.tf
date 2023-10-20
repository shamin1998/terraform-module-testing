# Defining AWS CloudWatch Terraform Resources

module "cloudwatch" {
  source = "../../../../../resources/cloudwatch"
  lambda_log_group_params = { function_name = var.lambda_function_name}
  rate_x_minutes_rule_params = { 
    name = "rate-${var.event_trigger_rate}-minute-rule-PUUID-${var.pipeline_uuid}"
    x = var.event_trigger_rate
    }
  
}

resource "aws_cloudwatch_event_target" "azure_blob_transfer_lambda_trigger_schedule" {
    rule = module.cloudwatch.rate_x_minutes_rule_outputs.name
    arn = var.lambda_function_arn
}

resource "aws_lambda_permission" "allow_cloudwatch_invoke_azure_blob_transfer" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = var.lambda_function_name
    principal = "events.amazonaws.com"
    source_arn = module.cloudwatch.rate_x_minutes_rule_outputs.arn
}
