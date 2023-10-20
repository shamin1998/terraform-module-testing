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
        function_name_prefix = optional(string,"destination-lambda")
        
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
        handler = "destination_oic_uploader.lambda_handler"
        scripts_path = "../../destination/oic-destination-adapter/src/"
    }
}

# variable s3_bucket_params {
#     type = object({
#         bucket_name = string
#         bucket_arn = string
#     })
# }

variable lambda_layers_params {
  type = object({
      layer_name = optional(string,"")
      layer_name_prefix = optional(string,"requests-layer")
      layer_requirements_path = string
    })

  default = {
    layer_requirements_path = "./modules/collectorless_pipeline/destination_adapters/s3_to_api/cisco_oic_uploader/layer_requirements.txt"
}
}
