variable pipeline_uuid {
    type = string
}

variable aws_region {
    type = string
}

variable asm_secret_name {
  type = string
}

variable lambda_function_params {
  type = object({
    function_name = optional(string,"")
    function_name_prefix = optional(string, "azure-blob-source-lambda")
    handler = string
    scripts_path = string
    layers = optional(list(string))

    temp_package_folder = optional(string,"python_lambda_package")
    package_filename = optional(string,"lambda_package.zip")
  })
}

variable state_table_name {
  type = string
}

variable azure_blob_storage_params {
  type = object({
      # azure_parent_folder_path = string
      azure_storage_account_name = optional(string)
      azure_container_name = optional(string)
      azure_parent_folder_path = optional(string)
    })

}

variable s3_bucket_params {
  type = object({
      s3_bucket_name = optional(string,"")
      s3_bucket_name_prefix = optional(string)
      s3_dest_folder_path = string
    })
}

variable lambda_layers_params {
  type = object({
    name = optional(string)
    layer_requirements_path = optional(string)
  })

  default = {
    name = "AzurePythonSDKLayer"
  }
}

variable sns_topic_params {
  type = object({
    name = optional(string,"")
    sns_topic_arn = string
  })
}