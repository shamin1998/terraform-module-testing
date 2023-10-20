# Defining AWS DynamoDB Terraform resources

locals {
  attributes = [{
      name = var.log_table.primary_index.hash_key
      type = "S"
    },
    {
      name = var.log_table.primary_index.range_key
      type = "S"
    }]
}

module "dynamodb" {
  source = "../../../../../resources/dynamodb"
  private_log_table_params = { 
    name = var.log_table.primary_index.name != "" ? var.log_table.primary_index.name : "${var.log_table.primary_index.name_prefix}-PUUID-${var.pipeline_uuid}"
    hash_key = var.log_table.primary_index.hash_key
    range_key = var.log_table.primary_index.range_key
    attributes = concat(local.attributes,[{ name = var.log_table.sort_index.range_key, type = "S" }])

    sort_index = {
      name = var.log_table.sort_index.name
      range_key = var.log_table.sort_index.range_key
      projection_type = var.log_table.sort_index.projection_type
      non_key_attributes = var.log_table.sort_index.non_key_attributes
    }

    optional_params = var.log_table.optional_params
  }
  
}
