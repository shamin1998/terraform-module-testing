variable pipeline_uuid {
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
    default = {}
}

variable environment {
    type = object({
        variables = map(string)
    })

    default = {
        variables = {}
    }
}

# variable aws_region {
#     type = string
# }

variable lambda_function_params {
    type = object({
        function_name = optional(string, "")
        function_name_prefix = optional(string,"transformer-lambda")
        
        handler = string
        scripts_path = string

        runtime = optional(string, "python3.10")
        # timeout = optional(number, 10)
        layers = optional(list(string),[])
        environment = optional(object({
            variables = optional(map(string))
        }),{})
        

    })

    default = {
        handler = "collectorless_transformer.lambda_handler"
        scripts_path = "../../transformer/src/"
    }
}

# variable s3_bucket_params {
#     type = object({
#         bucket_name = string
#         bucket_arn = string
#     })
# }

# variable lambda_layers_params {
#   type = object({
#       layer_name = optional(string,"")
#       layer_name_prefix = optional(string,"azure-sdk-layer")
#       layer_requirements_path = string
#     })

#   default = {
#     layer_requirements_path = "../terraform/source_adapters/cloud_data_import/azure_blob_reader/modules/layers/layer_requirements.txt"
# }
# }
