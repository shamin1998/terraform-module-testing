# AWS CloudWatch Terraform Resources
####################################

### Log Groups ###

# Create a log group for given Lambda Function
resource "aws_cloudwatch_log_group" "lambda_log_group" {

    name = "/aws/lambda/${var.function_name}"

    retention_in_days = var.retention_in_days
    skip_destroy = var.skip_destroy
}
