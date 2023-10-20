locals {
  lambda_function_name = coalesce(var.lambda_function_params.function_name, "${var.lambda_function_params.function_name_prefix}-puuid-${var.pipeline_uuid}")
}

module "azureSDKlayer" {
  source = "../../../resources/lambda/layers"

  layer_name = coalesce(var.lambda_layers_params.layer_name, "${var.lambda_layers_params.layer_name_prefix}-puuid-${var.pipeline_uuid}")
  layer_requirements_path = var.lambda_layers_params.layer_requirements_path
}

module "lambda_module" {
    source = "../../../modules/lambda/packager"

    function_name = local.lambda_function_name
    scripts_folder_path = var.lambda_function_params.scripts_path
    timeout = try(tonumber(var.params.timeout), 300) 
    
    handler = var.lambda_function_params.handler

    layers = [module.azureSDKlayer.layer_arn]

    environment = var.environment

    # aws_region = var.aws_region

    # asm_secret_name = var.asm_secret_name

    # # Lambda Terraform resource parameters
    # lambda_function_params = merge(var.lambda_function_params, { 
    #   function_name = local.lambda_function_name
    #   layers = [module.azureSDKlayer.layer_arn]
    #   })

    # # DynamoDB Table parameters
    # state_table_name = var.state_table_name
    # # {
    # #   name = module.dynamodb_module.log_table_name
    # #   hash_key = module.dynamodb_module.log_table_hash_key
    # #   range_key = module.dynamodb_module.log_table_range_key
    # #   sort_index = module.dynamodb_module.log_table_sort_index_name
    # #   timestamp_key = module.dynamodb_module.log_table_timestamp_key
    # # }

    # # Azure SDK parameters
    # azure_blob_storage_params = var.azure_blob_storage_params

    # # S3 Bucket parameters
    # s3_bucket_params = {
    #   s3_bucket_name = module.s3_module.bucket_name
    #   s3_dest_folder_path = module.s3_module.dest_folder_path
    # }

    # # SNS Topic parameters
    # sns_topic_params = { 
    #   sns_topic_arn = module.sns_module.topic_arn
    # }
}

module "cloudwatch_event" {
  count = var.trigger.type == "cloudwatch_event" ? 1 : 0
  source = "../../../resources/cloudwatch/event"

  name = "${var.trigger.name}-puuid-${var.pipeline_uuid}"

  function_name = local.lambda_function_name
  lambda_function_arn = module.lambda_module.function_arn
  depends_on = [ module.lambda_module ]
}

module "cloudwatch_logs" {
  source = "../../../resources/cloudwatch/logs"

  function_name = local.lambda_function_name
  
  depends_on = [ module.lambda_module ]
}


# module "iam_module" {
#   source = "./modules/iam"

#   pipeline_uuid = var.pipeline_uuid

#   asm_secret_arn = var.asm_secret_arn
#   dynamodb_table_arn = var.state_table_arn
#   # dynamodb_table_sort_index = var.state_table_params.sort_index
#   lambda_iam_role_id = module.lambda_module.iam_role_id
#   s3_bucket_arn = module.s3_module.bucket_arn
#   sns_topic_arn = module.sns_module.topic_arn
# }