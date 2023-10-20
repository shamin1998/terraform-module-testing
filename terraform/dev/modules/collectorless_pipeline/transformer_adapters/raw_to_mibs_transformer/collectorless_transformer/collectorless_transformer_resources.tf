locals {
    lambda_function_name = coalesce(var.lambda_function_params.function_name, "${var.lambda_function_params.function_name_prefix}-puuid-${var.pipeline_uuid}")
}

# module requests_layer {
#     source = "../../../resources/lambda/layers"

#     layer_name = coalesce(var.lambda_layers_params.layer_name, "${var.lambda_layers_params.layer_name_prefix}-puuid-${var.pipeline_uuid}")
#     layer_requirements_path = var.lambda_layers_params.layer_requirements_path
# }

module lambda_function {
    source = "../../../modules/lambda/packager"

    scripts_folder_path = var.lambda_function_params.scripts_path

    function_name = local.lambda_function_name
    handler = var.lambda_function_params.handler
    runtime = var.lambda_function_params.runtime
    timeout = try(tonumber(var.params.timeout), 300) 
    layers = [var.params.layer]
    environment = var.environment
    
}

## output testing_out {
#     value = module.lambda_function.layer_arn
# }

module s3_notification {
    count = var.trigger.type == "s3_event" ? 1 : 0
    source = "../../../resources/s3/bucket_notification"

    bucket_name = var.environment.variables.S3_SOURCE_TO_TRANSFORMER_BUCKET

    notify = "lambda"
    lambda_function_arn = module.lambda_function.function_arn
    bucket_arn = var.trigger.vars.arn

    depends_on = [ module.lambda_function ]
}

module sqs_trigger {
    count = var.trigger.type == "sqs_queue_message" ? 1 : 0
    source = "../../../resources/sqs/lambda_trigger"
    # enabled = true

    queue_arn = var.trigger.vars.arn
    lambda_function_arn = module.lambda_function.function_arn
}

# module allow_lambda_get_s3 {
#     source = "../../../resources/iam"

#     allow_lambda_access_s3_params = {
#         lambda_iam_role_id = module.lambda_function.function_role_id
#         actions = ["s3:GetObject", "s3:ListBucket"]
#         resources = ["${var.s3_bucket_params.bucket_arn}/*", var.s3_bucket_params.bucket_arn]
#     }
# }

module "cloudwatch_logs" {
  source = "../../../resources/cloudwatch/logs"

  function_name = local.lambda_function_name
  
  depends_on = [ module.lambda_function ]
}
