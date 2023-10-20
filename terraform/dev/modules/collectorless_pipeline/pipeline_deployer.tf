# Create pipeline Terraform resources

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.67"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# # Admin

# output write_capacity_value {
#   value = var.state_table.write_capacity
# }

# Shared Resources

locals {

  # shared_params = jsonencode([
  #     for key in sort(keys(var.shared_params)) : {
  #       key = lookup(var.shared_params, key)
  #   }])

  shared_params = { for k, v in var.shared_params : k => replace(v, "{PIPELINE_UUID}", var.pipeline_uuid) }

}

module "dynamodb_state_table" {
  count = var.state_table.enable ? 1 : 0

  source = "./resources/dynamodb"
  
  name = coalesce(var.state_table.name, local.shared_params.DYNAMODB_TABLE_NAME)
  hash_key = var.state_table.hash_key
  range_key = var.state_table.range_key
  attributes = var.state_table.attributes

  global_secondary_indexes = var.state_table.global_secondary_indexes
  local_secondary_indexes = var.state_table.local_secondary_indexes

  billing_mode = var.state_table.billing_mode
  read_capacity = var.state_table.read_capacity
  write_capacity = 20
  
  stream_enabled = var.state_table.stream_enabled
  stream_view_type = var.state_table.stream_view_type
}

module "source_to_transformer_s3_bucket" {
    count = try(local.shared_params.S3_SOURCE_TO_TRANSFORMER_BUCKET, "") != "" ? 1 : 0
    source = "./resources/s3/bucket"

    pipeline_uuid = var.pipeline_uuid

    bucket_name = local.shared_params.S3_SOURCE_TO_TRANSFORMER_BUCKET
    
}

module "transformer_to_destination_s3_bucket" {
    count = try(local.shared_params.S3_TRANSFORMER_TO_DESTINATION_BUCKET, "") != "" ? 1 : 0
    source = "./resources/s3/bucket"

    pipeline_uuid = var.pipeline_uuid

    bucket_name = local.shared_params.S3_TRANSFORMER_TO_DESTINATION_BUCKET
    
}

module "sqs_source_to_transformer_queue" {
  count = try(local.shared_params.SQS_SOURCE_TO_TRANSFORMER_QUEUE, "") != "" ? 1 : 0
  source = "./resources/sqs/queue"
  
  # pipeline_uuid = var.pipeline_uuid
  queue_create = true
  queue_name = local.shared_params.SQS_SOURCE_TO_TRANSFORMER_QUEUE
  
}

module "sqs_transformer_to_destination_queue" {
  count = try(local.shared_params.SQS_TRANSFORMER_TO_DESTINATION_QUEUE, "") != "" ? 1 : 0
  source = "./resources/sqs/queue"
  
  # pipeline_uuid = var.pipeline_uuid
  queue_create = true
  queue_name = local.shared_params.SQS_TRANSFORMER_TO_DESTINATION_QUEUE
  
}


# For testing purposes till AWS Secret Manager Terraform module is implemented
locals {
  secret_arn = "arn:aws:secretsmanager:us-east-1:116184061575:secret:DTE_Secret-r2BwRT"
}

# Source

# locals {
#   source_env = flatten([ for var_name, var_value in var.source_def.env:
#   {
#     var_name = replace(var_value, "{PIPELINE_UUID}", var.pipeline_uuid) 
#   }
#                        ])
# }


module source_adapter {
    count = var.source_def.enable ? 1 : 0

    source = "./source_adapters"

    pipeline_uuid = var.pipeline_uuid
    aws_region = var.aws_region

    type = var.source_def.type
    name = var.source_def.name

    trigger = var.source_def.trigger[0]

    params = var.source_def.params
    environment = {
      variables = merge( local.shared_params, var.source_def.env, { PIPELINE_UUID = var.pipeline_uuid, SQS_QUEUE_URL = module.sqs_source_to_transformer_queue[0].sqs_queue_url } )
    }
    # merge(var.source_def.params, { 
    #   DYNAMODB_TABLE_NAME = var.source_vars.source_params.DYNAMODB_TABLE_NAME == "shared_resources.state_table" ? module.dynamodb_state_table[0].name : ""
    #   PIPELINE_UUID = var.pipeline_uuid
    #   asm_secret_arn = local.secret_arn 
    #   }) # module.secret_group[0].arn

    # state_table_name = module.dynamodb_state_table[0].name
    # asm_secret_arn = local.secret_arn   # module.secret_group[0].arn
    # state_table_arn = module.dynamodb_state_table[0].table_arn


}

# Source IAM Lambda Permission

module source_lambda_iam_permissions {
  count = var.source_def.enable ? 1 : 0
  source = "./resources/iam"

  pipeline_uuid = var.pipeline_uuid

  lambda_iam_role_id = module.source_adapter[0].lambda_id
}

# Transformer

locals {
  transformer_vars = var.transformer_def.enable ? merge(var.transformer_def.trigger[0].vars, { arn = module.sqs_source_to_transformer_queue[0].sqs_queue_arn }) : {}
}

locals {
  transformer_trigger = var.transformer_def.enable ? {
    type = var.transformer_def.trigger[0].type
    name = var.transformer_def.trigger[0].name
    vars = local.transformer_vars
  } : {
    type = ""
    name = ""
    vars = {}
  }
}


module transformer_adapter {
    count = var.transformer_def.enable ? 1 : 0

    source = "./transformer_adapters"

    pipeline_uuid = var.pipeline_uuid
    aws_region = var.aws_region

    type = var.transformer_def.type
    name = var.transformer_def.name

    trigger = local.transformer_trigger

    params = var.transformer_def.params
    environment = {
      variables = merge( local.shared_params, var.transformer_def.env, { PIPELINE_UUID = var.pipeline_uuid, SQS_QUEUE_URL = module.sqs_transformer_to_destination_queue[0].sqs_queue_url } )
    }
    # merge(var.transformer_def.params, { 
    #   DYNAMODB_TABLE_NAME = var.transformer_vars.transformer_params.DYNAMODB_TABLE_NAME == "shared_retransformers.state_table" ? module.dynamodb_state_table[0].name : ""
    #   PIPELINE_UUID = var.pipeline_uuid
    #   asm_secret_arn = local.secret_arn 
    #   }) # module.secret_group[0].arn

    # state_table_name = module.dynamodb_state_table[0].name
    # asm_secret_arn = local.secret_arn   # module.secret_group[0].arn
    # state_table_arn = module.dynamodb_state_table[0].table_arn
    depends_on = [ module.transformer_to_destination_s3_bucket ]


}

# transformer IAM Lambda Permission

module transformer_lambda_iam_permissions {
  count = var.transformer_def.enable ? 1 : 0
  source = "./resources/iam"

  pipeline_uuid = var.pipeline_uuid

  lambda_iam_role_id = module.transformer_adapter[0].lambda_id
}

# output testing_out {
#   value = module.transformer_adapter[0].testing_out
# }

# # Destination

locals {
  destination_vars = var.destination_def.enable ? merge(var.destination_def.trigger[0].vars, { arn = module.sqs_transformer_to_destination_queue[0].sqs_queue_arn }) : {}
}

locals {
  destination_trigger = var.destination_def.enable ? {
    type = var.destination_def.trigger[0].type
    name = var.destination_def.trigger[0].name
    vars = local.destination_vars
  } : {
    type = ""
    name = ""
    vars = {}
  }
}

module destination_adapter {
    count = var.destination_def.enable ? 1 : 0

    source = "./destination_adapters"

    pipeline_uuid = var.pipeline_uuid
    aws_region = var.aws_region

    type = var.destination_def.type
    name = var.destination_def.name

    trigger = local.destination_trigger

    params = var.destination_def.params
    environment = {
      variables = merge( local.shared_params, var.destination_def.env, { PIPELINE_UUID = var.pipeline_uuid } )
    }
    # merge(var.destination_def.params, { 
    #   DYNAMODB_TABLE_NAME = var.destination_vars.destination_params.DYNAMODB_TABLE_NAME == "shared_redestinations.state_table" ? module.dynamodb_state_table[0].name : ""
    #   PIPELINE_UUID = var.pipeline_uuid
    #   asm_secret_arn = local.secret_arn 
    #   }) # module.secret_group[0].arn

    # state_table_name = module.dynamodb_state_table[0].name
    # asm_secret_arn = local.secret_arn   # module.secret_group[0].arn
    # state_table_arn = module.dynamodb_state_table[0].table_arn
    depends_on = [ module.transformer_to_destination_s3_bucket ]


}

# Destination IAM Lambda Permission

module destination_lambda_iam_permissions {
  count = var.destination_def.enable ? 1 : 0
  source = "./resources/iam"

  pipeline_uuid = var.pipeline_uuid

  lambda_iam_role_id = module.destination_adapter[0].lambda_id
}

# output testing_out {
#   value = module.destination_adapter[0].testing_out
# }
