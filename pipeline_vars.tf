### Shared Parameters ###

variable pipeline_uuid {
    default = "123456789"
}

variable aws_region {
    type = string
}

variable shared_params {
    type = map(string)
}

variable source_def {
    type = object({ enable = optional(bool, true)
        type = string
        name = string
        version = optional(number)

        trigger = optional(list(object({
            type = string
            name = string
            vars = map(string)
        })))

        params = optional(map(string))

        env = optional(map(string))
    })

    default = { enable = false
        type = ""
        name = ""
    }
}

variable transformer_def {
    type = object({ enable = optional(bool, true)
        type = string
        name = string
        version = optional(number)

        trigger = optional(list(object({
            type = string
            name = string
            vars = map(string)
        })))

        params = optional(map(string))

        env = optional(map(string))
    })

    default = { enable = false
        type = ""
        name = ""
    }
}

variable destination_def {
    type = object({ enable = optional(bool, true)
        type = string
        name = string
        version = optional(number)

        trigger = optional(list(object({
            type = string
            name = string
            vars = map(string)
        })))

        params = optional(map(string))

        env = optional(map(string))
    })

    default = { enable = false
        type = ""
        name = ""
    }
}

# variable "aws_region" {
#   description = "The AWS region to create things in."
#   type = string
# #   default     = "us-east-1"
# }

# variable pipeline_uuid {
#     default = "123456789"
# }

# ### Shared Resource Parameters ###

# # variable state_table_params {
# #     type = string
# # }

# variable secret_name {
#     type = string
# }

variable state_table {
    type = object({ enable = optional(bool, true)
        name = optional(string, "")
        name_prefix = optional(string, "state_table")
        hash_key = optional(string, "adapter_name")
        range_key = optional(string, "log_timestamp")
        attributes = optional(list(object({ type = string, name = string})),
            [ 
                {
                    type = "S"
                    name = "pipeline_uuid"
                },
                {
                    type = "S"
                    name = "log_timestamp"
                },
                {
                    type = "S"
                    name = "adapter_name"
                },
                {
                    type = "S"
                    name = "input_path"
                }
            ])


        global_secondary_indexes = optional(list(object({
            name = string
            hash_key = optional(string)
            range_key = optional(string)
            projection_type = optional(string, "KEYS_ONLY")
            non_key_attributes = optional(list(string))
        })), 
        [ {
            name = "pipelineIndex"
            hash_key = "pipeline_uuid"
            range_key = "log_timestamp"
            projection_type = "ALL"
            # non_key_attributes = [""]
        }])

        local_secondary_indexes = optional(list(object({
            name = string
            range_key = string
            projection_type = optional(string, "KEYS_ONLY")
            non_key_attributes = optional(list(string))
        })), 
        [ {
          name = "inputIndex"
          range_key = "input_path"
          projection_type = "INCLUDE"
          non_key_attributes = ["log_timestamp"]
        } ])

        billing_mode = optional(string, "PROVISIONED")
        read_capacity = optional(number, 20)
        write_capacity = optional(number, 20)
        stream_enabled = optional(bool, false)
        stream_view_type = optional(string, "")
    })

    default = { enable = false   # Set to false for prod
        name_prefix = "state_table"
        hash_key = "adapter_name"
        range_key = "log_timestamp"
        attributes = [ {
          type = "S"
          name = "pipeline_uuid"
        },
        # {
        #   type = "S"
        #   name = "run_id"
        # },
        {
          type = "S"
          name = "log_timestamp"
        },
        {
          type = "S"
          name = "adapter_name"
        },
        {
          type = "S"
          name = "input_path"
        }
        # {
        #   type = "S"
        #   name = "adapter_state"
        # },
        # {
        #   type = "S"
        #   name = "description"
        # }
         ]

        global_secondary_indexes = [ {
            name = "pipelineIndex"
            hash_key = "pipeline_uuid"
            range_key = "log_timestamp"
            projection_type = "ALL"
            # non_key_attributes = [""]
        }]

        local_secondary_indexes = [ {
          name = "inputIndex"
          range_key = "input_path"
          projection_type = "INCLUDE"
          non_key_attributes = ["log_timestamp"]
        } ]

        billing_mode = "PROVISIONED"
        read_capacity = 20
        write_capacity = 20
    }
}

# ### Source Parameters ###

# variable source_vars {
#     description = "Variables to specify which source adapter module to create, and its parameters."

#     type = object({ enable_source = optional(bool, true)
#         source_type = string
#         source_name = string
#         source_params = map(string)
#     })

#     default = { enable_source = false
#         source_type = "cloud_data_import"
#         source_name = "azure_blob_reader"
#         source_params = {
#                 asm_secret_name = "DTE_Secret"
#                 # asm_secret_arn = "arn:aws:secretsmanager:us-east-1:116184061575:secret:DTE_Secret-r2BwRT"

#                 # azure_container_url = "https://shamincisco.blob.core.windows.net/blob-container?sp=rl&st=2023-07-19T16:14:07Z&se=2023-08-26T00:14:07Z&sv=2022-11-02&sr=c&sig=YUHbrySyV5odINiA%2BWFMvpe0zAhFKiELV%2BKkeJcN5gE%3D"
#                 # azure_parent_folder_path = "testing_blob"

#                 # azure_storage_account_name = "shamincisco"
#                 # azure_container_name = "blob-container"          
#                 # azure_sas_token = "sp=rl&st=2023-07-19T16:14:07Z&se=2023-08-26T00:14:07Z&sv=2022-11-02&sr=c&sig=YUHbrySyV5odINiA%2BWFMvpe0zAhFKiELV%2BKkeJcN5gE%3D"
#         }
#     }
# }

# variable transformer_vars {
#     description = "Variables to specify which transformer adapter module to create, and its parameters."

#     type = object({ enable_transformer = optional(bool, true)
#         transformer_type = string
#         transformer_name = string
#         transformer_params = map(string)
#     })

#     default = { enable_transformer = false
#         transformer_type = ""
#         transformer_name = ""
#         transformer_params = {
#                 lambda_function_handler_name = ""
#                 lambda_function_scripts_path = ""
#         }
#     }
# }

# variable destination_vars {
#     description = "Variables to specify which destination adapter module to create, and its parameters."

#     type = object({ enable_destination = optional(bool, true)
#         destination_type = string
#         destination_name = string
#         destination_params = map(string)
#     })

#     default = { enable_destination = false
#         destination_type = "s3_to_api"
#         destination_name = "cisco_oic_uploader"
#         destination_params = {
#                 asm_secret_name = "DTE_Secret"
#                 asm_secret_arn = "arn:aws:secretsmanager:us-east-1:116184061575:secret:DTE_Secret-r2BwRT"

#                 lambda_function_name = ""
#                 lambda_function_handler = "s3_to_oic.lambda_handler"
#                 lambda_function_scripts_path = "../oic_destination_adapter/src/"

#                 s3_bucket_name = "test-blob-storage-bucket"
#                 s3_bucket_arn = "arn:aws:s3:::test-blob-storage-bucket"
#         }
#     }
# }