### Pipeline Parameters ###

variable "pipeline_uuid" {
  description = "Pipeline Universal Unique Identifier"
  type = string
}

variable trigger {
  type = object({
    type = string
    name = string
    vars = optional(map(string))
  })
}

variable params {
  type = map(string)

  default = { }
    
}

variable environment {
  type = object({
    variables = map(string)
  })

  default = {
    variables = { }
  }
}


# variable aws_region {
#     type = string
# }

# variable asm_secret_name {
#   type = string
# }

# variable asm_secret_arn {
#   type = string
# }

# ### State Table Variables ###

# variable state_table_name {
#   type = string
# }

# variable state_table_arn {
#   type = string
# }

# ### Source Adapter Variables ###

variable lambda_function_params {
  description = "Parameters for the Lambda Function module variables, ex. Azure container name, S3 bucket name, credentials, etc."

  type = object({
      function_name = optional(string,"")
      function_name_prefix = optional(string, "source-lambda")
      handler = string
      scripts_path = string

      temp_package_folder = optional(string,"python_lambda_package")
      package_filename = optional(string,"lambda_package.zip")
    })

    default = {
      handler = "azure_blob_transfer.lambda_handler"
      scripts_path = "../../source/azure-blob-source/src/"
    }
}

# variable azure_blob_storage_params {
#   type = object({
#       # azure_parent_folder_path = string
#       azure_storage_account_name = optional(string)
#       azure_container_name = optional(string)
#       azure_parent_folder_path = optional(string, "")
#     })

#   default = {
#     azure_storage_account_name = ""
#   }
# }

variable lambda_layers_params {
  type = object({
      layer_name = optional(string,"")
      layer_name_prefix = optional(string,"azure-sdk")
      layer_requirements_path = string
    })

  default = {
    layer_requirements_path = "./modules/collectorless_pipeline/source_adapters/cloud_data_import/azure_blob_reader/modules/layers/layer_requirements.txt"
}
}

# variable dynamodb_table_params {
#   type = object({
#     log_table = optional(object({
#       primary_index = map(string)

#       sort_index = optional(object({
#         name = string
#         range_key = string
#         projection_type = optional(string)
#         non_key_attributes = optional(list(string))
#       }))
      
#       optional_params = optional(map(string))
#     }))
#   })

#   default = {
#     log_table = {
#       primary_index = {
#         hash_key = "azure_parent_folder_path"
#         range_key = "azure_source_path"
#       }

#       sort_index = {
#         name = "timestamp_sort_index"
#         range_key = "log_timestamp"
#       }

#     }
#   }
# }

# variable s3_bucket_params {
#   type = object({
#       s3_bucket_name = optional(string)
#       s3_bucket_name_prefix = optional(string, "azure-blob-source-bucket")
#       s3_dest_folder_path = optional(string, "azure_blob_reader_data/")
#     })

#   default = {
#     s3_bucket_name = ""
#   }
# }

# variable sns_topic_params {
#   type = object({
#       sns_topic_name = optional(string)
#       sns_topic_name_prefix = optional(string, "trigger-transformer-topic")
#     })

#   default = {
#     sns_topic_name = ""
#   }
# }